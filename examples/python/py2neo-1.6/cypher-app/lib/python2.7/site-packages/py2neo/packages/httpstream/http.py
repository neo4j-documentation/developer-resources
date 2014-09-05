#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013-2014, Nigel Small
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import unicode_literals

from base64 import b64encode
import errno
try:
    from http.client import (BadStatusLine, CannotSendRequest,
                             HTTPConnection as _HTTPConnection,
                             HTTPSConnection as _HTTPSConnection,
                             HTTPException, ResponseNotReady,
                             responses)
except ImportError:
    from httplib import (BadStatusLine, CannotSendRequest,
                         HTTPConnection as _HTTPConnection,
                         HTTPSConnection as _HTTPSConnection,
                         HTTPException, ResponseNotReady,
                         responses)
import json
import logging
from os import strerror
from socket import error, gaierror, herror, timeout, IPPROTO_TCP, TCP_NODELAY
from threading import local
import sys
from xml.dom.minidom import parseString

from py2neo.packages.jsonstream import JSONStream
from py2neo.packages.urimagic import URI, URITemplate
from py2neo.packages.urimagic.kvlist import KeyValueList  # no point in another copy

from . import __version__
from .jsonencoder import JSONEncoder
from .numbers import *


__all__ = ["NetworkAddressError", "SocketError", "RedirectionError", "Request",
           "Response", "Redirection", "ClientError", "ServerError", "Resource",
           "ResourceTemplate", "get", "put", "post", "delete", "head"]


class HTTPConnection(_HTTPConnection):
    """ Patched class to avoid Nagle's algorithm:
    https://en.wikipedia.org/wiki/Nagle%27s_algorithm
    """

    def connect(self):
        _HTTPConnection.connect(self)
        self.sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)


class HTTPSConnection(_HTTPSConnection):
    """ Patched class to avoid Nagle's algorithm:
    https://en.wikipedia.org/wiki/Nagle%27s_algorithm
    """

    def connect(self):
        _HTTPSConnection.connect(self)
        self.sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)


connection_classes = {
    "http": HTTPConnection,
    "https": HTTPSConnection,
}

default_encoding = "ISO-8859-1"
default_chunk_size = 4096

log = logging.getLogger(__name__)
try:
    log.addHandler(logging.NullHandler())
except AttributeError:
    # Python 2.6
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass
    log.addHandler(NullHandler())

redirects = {}

# Since the Python docs state that "symbols that are not used on the current
# platform are not defined by the module" we have to import error codes
# cautiously. Error numbers also vary across platforms so we cannot rely on
# raw numeric values either.
retry_codes = {}
if hasattr(errno, "EPIPE"):
    retry_codes[errno.EPIPE] = "broken pipe"
if hasattr(errno, "ENETRESET"):
    retry_codes[errno.ENETRESET] = "network reset"
if hasattr(errno, "ECONNABORTED"):
    retry_codes[errno.ECONNABORTED] = "connection aborted"
if hasattr(errno, "ECONNRESET"):
    retry_codes[errno.ECONNRESET] = "connection reset"

supports_buffering = ((2, 7) <= sys.version_info < (2, 8))


def user_agent(product=None):
    ua = []
    if product:
        if isinstance(product, (tuple, list)):
            ua.append("/".join(map(str, product)))
        else:
            ua.append(str(product))
    ua.append("HTTPStream/{0}".format(__version__))
    ua.append("Python/{0}.{1}.{2}-{3}-{4}".format(*sys.version_info))
    ua.append("({0})".format(sys.platform))
    return " ".join(ua)


class Loggable(object):

    def __init__(self, cls, message):
        log.error("!!! {0}: {1}".format(cls.__name__, message))


class NetworkAddressError(Loggable, IOError):

    def __init__(self, message, host_port=None):
        self._host_port = host_port
        IOError.__init__(self, message)
        Loggable.__init__(self, self.__class__, message)

    @property
    def host_port(self):
        return self._host_port


class SocketError(Loggable, IOError):

    def __init__(self, code, description, host_port=None):
        self._code = code
        self._description = description
        self._host_port = host_port
        IOError.__init__(self, description)
        Loggable.__init__(self, self.__class__, description)

    @property
    def code(self):
        return self._code

    @property
    def description(self):
        return self._description

    @property
    def host_port(self):
        return self._host_port


class RedirectionError(Loggable, HTTPException):

    def __init__(self, *args, **kwargs):
        HTTPException.__init__(self, *args, **kwargs)
        Loggable.__init__(self, self.__class__, args[0])


class ConnectionPuddle(local):
    """ A collection of HTTP/HTTPS connections to a single network location
    (i.e. host:port). Connections may be acquired and will be created if
    necessary; after use, these must be released.
    """

    def __init__(self, connection_class, host_port):
        local.__init__(self)
        self.__connection_class = connection_class
        self.__host_port = host_port
        self.__active = []
        self.__passive = []

    @property
    def host_port(self):
        return self.__host_port

    @property
    def connection_class(self):
        return self.__connection_class

    def __repr__(self):
        return "<{0}({1}) active={2} passive={3}>".format(
            self.__connection_class.__name__, repr(self.host_port),
            len(self.__active), len(self.__passive)
        )

    def __hash__(self):
        return hash((self.__connection_class, self.host_port))

    def __len__(self):
        return len(self.__active) + len(self.__passive)

    def acquire(self):
        if self.__passive:
            connection = self.__passive.pop()
        else:
            connection = self.__connection_class(self.host_port)
        self.__active.append(connection)
        return connection

    def release(self, connection):
        try:
            self.__active.remove(connection)
        except ValueError:
            pass
        if len(self.__passive) < 2:
            self.__passive.append(connection)
        else:
            connection.close()


class ConnectionPool(object):
    """ A collection of :py:class:`ConnectionPuddle` objects for various
    network locations.
    """

    _puddles = {}

    @classmethod
    def _get_puddle(cls, connection_class, host_port):
        key = (connection_class, host_port)
        if key not in cls._puddles:
            cls._puddles[key] = ConnectionPuddle(connection_class, host_port)
        return cls._puddles[key]

    @classmethod
    def acquire(cls, scheme, host_port):
        puddle = cls._get_puddle(connection_classes[scheme], host_port)
        return puddle.acquire()

    @classmethod
    def release(cls, connection):
        puddle = cls._get_puddle(connection.__class__, "{0}:{1}".format(
            connection.host, connection.port))
        puddle.release(connection)


def submit(method, uri, body, headers):
    """ Submit one HTTP request.
    """
    uri = URI(uri)
    headers["Host"] = uri.host_port
    if uri.user_info:
        credentials = uri.user_info.encode("UTF-8")
        value = "Basic " + b64encode(credentials).decode("ASCII")
        headers["Authorization"] = value
    try:
        http = ConnectionPool.acquire(uri.scheme, uri.host_port)
    except KeyError:
        raise ValueError("Unsupported URI scheme " + repr(uri.scheme))

    def send(reconnect=None):
        if reconnect:
            log.debug("<~> Reconnecting ({0})".format(reconnect))
            http.close()
            http.connect()
        if method in ("GET", "DELETE") and not body:
            log.info(">>> {0} {1}".format(method, uri))
        elif body:
            log.info(">>> {0} {1} [{2}]".format(method, uri, len(body)))
        else:
            log.info(">>> {0} {1} [0]".format(method, uri))
        if __debug__:
            for key, value in headers.items():
                log.debug(">>> {0}: {1}".format(key, value))
        http.request(method, uri.absolute_path_reference, body, headers)
        if supports_buffering:
            return http.getresponse(buffering=True)
        else:
            return http.getresponse()

    try:
        try:
            response = send()
        except BadStatusLine as err:
            if err.line == "''":
                response = send("peer closed connection")
            else:
                raise
        except ResponseNotReady:
            response = send("response not ready")
        except timeout:
            response = send("timeout")
        except error as err:
            if isinstance(err.args[0], tuple):
                code = err.args[0][0]
            else:
                code = err.args[0]
            if code in retry_codes:
                response = send(retry_codes[code])
            else:
                raise
    except (gaierror, herror) as err:
        raise NetworkAddressError(err.args[1], host_port=uri.host_port)
    except error as err:
        if isinstance(err.args[0], tuple):
            code, description = err.args[0]
        elif isinstance(err.args[0], int):
            code = err.args[0]
            try:
                description = strerror(code)
            except ValueError:
                description = None
        else:
            code, description = None, err.args[0]
        if code == 2:
            # Workaround for Linux bug with incorrect error message on
            # host resolution
            # ----
            # https://bugs.launchpad.net/ubuntu/+source/eglibc/+bug/1154599
            raise NetworkAddressError("Name or service not known",
                                      host_port=uri.host_port)
        else:
            raise SocketError(code, description, host_port=uri.host_port)
    else:
        return http, response


class Request(object):

    def __init__(self, method, uri, body=None, headers=None):
        if not uri:
            raise ValueError("No URI specified for request")
        #: HTTP method of this request
        self.method = method
        self.uri = uri
        self._headers = dict(headers or {})
        self.body = body

    @property
    def __uri__(self):
        return self.uri

    @property
    def uri(self):
        """ URI of the request.
        """
        return self._uri

    @uri.setter
    def uri(self, value):
        self._uri = URI(value)

    @property
    def body(self):
        """ Content of the request.
        """
        if isinstance(self._body, (dict, list, tuple)):
            return json.dumps(self._body, cls=JSONEncoder,
                              separators=(",", ":"))
        else:
            return self._body

    @body.setter
    def body(self, value):
        self._body = value

    @property
    def headers(self):
        """ Dictionary of headers attached to the request.
        """
        if isinstance(self._body, (dict, list, tuple)):
            self._headers.setdefault("Content-Type", "application/json")
        return self._headers

    def submit(self, redirect_limit=0, product=None, **response_kwargs):
        """ Submit this request and return a
        :py:class:`Response <httpstream.Response>` object.
        """
        uri = URI(self.uri)
        headers = dict(self.headers)
        headers.setdefault("User-Agent", user_agent(product))
        while True:
            http, rs = submit(self.method, uri, self.body, headers)
            status_class = rs.status // 100
            if status_class == 3:
                redirection = Redirection(http, uri, self, rs,
                                          **response_kwargs)
                if redirect_limit:
                    redirect_limit -= 1
                    location = URI.resolve(uri, rs.getheader("Location"))
                    if location == uri:
                        raise RedirectionError("Circular redirection")
                    if rs.status in (MOVED_PERMANENTLY, PERMANENT_REDIRECT):
                        redirects[uri] = location
                    uri = location
                    redirection.close()
                else:
                    return redirection
            elif status_class == 4:
                raise ClientError(http, uri, self, rs, **response_kwargs)
            elif status_class == 5:
                raise ServerError(http, uri, self, rs, **response_kwargs)
            else:
                return Response(http, uri, self, rs, **response_kwargs)


class Response(object):
    """ File-like object allowing consumption of an HTTP response.
    """

    def __init__(self, http, uri, request, response, **kwargs):
        self._http = http
        self._uri = URI(uri)
        self._request = request
        self._response = response
        self._reason = kwargs.get("reason")
        self.__headers = KeyValueList(self._response.getheaders())
        #: Default chunk size for this response
        self.chunk_size = kwargs.get("chunk_size", default_chunk_size)
        log.info("<<< {0}".format(self))
        if __debug__:
            for key, value in self._response.getheaders():
                log.debug("<<< {0}: {1}".format(key, value))

    def __del__(self):
        self.close()

    def __repr__(self):
        if self.is_chunked:
            return "{0} {1} [chunked]".format(self.status_code, self.reason)
        else:
            return "{0} {1} [{2}]".format(self.status_code, self.reason,
                                          self.content_length)

    def __getitem__(self, key):
        if not self._response:
            return None
        return self._response.getheader(key)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    @property
    def closed(self):
        """ Indicates whether or not the response is closed.
        """
        return not bool(self._http)

    def close(self):
        """ Close the response, discarding all remaining content and releasing
        the underlying connection object.
        """
        if self._http:
            try:
                self._response.read()
            except HTTPException:
                pass
            ConnectionPool.release(self._http)
            self._http = None

    @property
    def __uri__(self):
        return self._uri

    @property
    def uri(self):
        """ The URI from which the response came.
        """
        return self._uri

    @property
    def request(self):
        """ The :py:class:`Request` object which preceded this response.
        """
        return self._request

    @property
    def status_code(self):
        """ The status code of the response
        """
        return self._response.status

    @property
    def reason(self):
        """ The reason phrase attached to this response.
        """
        if self._reason:
            return self._reason
        else:
            return responses[self.status_code]

    @property
    def headers(self):
        """ The response headers.
        """
        return self.__headers

    @property
    def content_length(self):
        """ The length of content as provided by the `Content-Length` header
        field. If the content is chunked, this returns :py:const:`None`.
        """
        if not self.is_chunked:
            return int(self._response.getheader("Content-Length", 0))

    @property
    def content_type(self):
        """ The type of content as provided by the `Content-Type` header field.
        """
        try:
            content_type = [
                _.strip()
                for _ in self._response.getheader("Content-Type").split(";")
            ]
        except AttributeError:
            return None
        return content_type[0]

    @property
    def encoding(self):
        """ The content character set encoding.
        """
        try:
            content_type = dict(
                _.strip().partition("=")[0::2]
                for _ in self._response.getheader("Content-Type").split(";")
            )
        except AttributeError:
            return default_encoding
        return content_type.get("charset", default_encoding)

    @property
    def is_chunked(self):
        """ Indicates whether or not the content is chunked.
        """
        return self._response.getheader("Transfer-Encoding") == "chunked"

    @property
    def is_json(self):
        """ Indicates whether or not the content is JSON.
        """
        return self.content_type in ("application/json",
                                     "application/x-javascript",
                                     "text/javascript",
                                     "text/json")

    @property
    def json(self):
        """ Fetch all content, decoding from JSON and returning the decoded
        value.
        """
        if not self.is_json:
            raise TypeError("Content is not JSON")
        return json.loads(self.read().decode(self.encoding))

    @property
    def is_text(self):
        """ Indicates whether or not the content is plain text.
        """
        return self.content_type.partition("/")[0] == "text"

    @property
    def text(self):
        """ Fetches all content as a string.
        """
        if not self.is_text and not self.is_json and not self.is_xml:
            raise TypeError("Content is not text")
        return self.read().decode(self.encoding)

    @property
    def is_tsj(self):
        """ Indicates whether or not the content is tab-separated JSON.
        """
        return self.content_type == "text/x-tab-separated-json"

    @property
    def tsj(self):
        """ Fetches all content, decoding from tab-separated JSON and returning
        the decoded values.
        """
        if not self.is_tsj:
            raise TypeError("Content is not tab-separated JSON")
        return [
            [json.loads(value) for value in line.split("\t")]
            for line in self.read().decode(self.encoding).splitlines()
        ]

    @property
    def is_xml(self):
        """ Indicates whether or not the content is XML.
        """
        return self.content_type == "application/xml"

    @property
    def dom(self):
        """ Fetches all content, decoding from XML and returning as a DOM
        object.
        """
        if not self.is_xml:
            raise TypeError("Content is not XML")
        return parseString(self.read().decode(self.encoding))

    @property
    def content(self):
        """ Fetch all content, returning a value appropriate for the content
        type.
        """
        if self.status_code == NO_CONTENT:
            return None
        elif self.is_json:
            return self.json
        elif self.is_tsj:
            return self.tsj
        elif self.is_text:
            return self.text
        else:
            return self.read()

    def read(self, size=None):
        """ Fetch some or all of the response content, returning as a bytearray.
        """
        completed = False
        try:
            if size is None:
                data = self._response.read()
                completed = True
            else:
                data = self._response.read(size)
                completed = bool(size and not data)
            return data
        finally:
            if completed:
                self.close()

    def iter_chunks(self, chunk_size=None):
        """ Iterate through the content as chunks of text. Chunk sizes may vary
        slightly from that specified due to multi-byte characters. If no chunk
        size is specified, a default of 4096 is used.
        """
        try:
            if not chunk_size:
                chunk_size = self.chunk_size
            pending = bytearray()
            data = True
            while data:
                data = self.read(chunk_size)
                pending.extend(data)
                decoded = None
                while data and not decoded:
                    try:
                        decoded = pending.decode(self.encoding)
                    except UnicodeDecodeError:
                        data = self.read(1)
                        pending.extend(data)
                    else:
                        del pending[:]
                        yield decoded
        finally:
            self.close()

    def iter_json(self):
        """ Iterate through the content as individual JSON values.
        """
        return iter(JSONStream(self.iter_chunks()))

    def iter_lines(self, keep_ends=False):
        """ Iterate through the content as lines of text.
        """
        data = ""
        for chunk in self.iter_chunks():
            data += chunk
            while "\r" in data or "\n" in data:
                cr, lf = data.find("\r"), data.find("\n")
                if cr >= 0 and lf == cr + 1:
                    eol_pos, eol_len = cr, 2
                else:
                    if cr >= 0 and lf >= 0:
                        eol_pos = min(cr, lf)
                    else:
                        eol_pos = cr if cr >= 0 else lf
                    eol_len = 1
                x = eol_pos + eol_len
                if keep_ends:
                    line, data = data[:x], data[x:]
                else:
                    line, data = data[:eol_pos], data[x:]
                yield line
        if data:
            yield data

    def iter_tsj(self):
        """ Iterate through the content as lines of tab-separated JSON.
        """
        for line in self.iter_lines():
            yield [json.loads(value) for value in line.split("\t")]

    def __iter__(self):
        if self.status_code == NO_CONTENT:
            return iter([])
        elif self.is_json:
            return self.iter_json()
        elif self.is_tsj:
            return self.iter_tsj()
        elif self.is_text:
            return self.iter_lines()
        else:
            return self.iter_chunks()


class Redirection(Response):

    def __init__(self, http, uri, request, response, **kwargs):
        assert response.status // 100 == 3
        Response.__init__(self, http, uri, request, response, **kwargs)


class ClientError(Exception, Response):

    def __init__(self, http, uri, request, response, **kwargs):
        assert response.status // 100 == 4
        Response.__init__(self, http, uri, request, response, **kwargs)
        Exception.__init__(self, self.reason)


class ServerError(Exception, Response):

    def __init__(self, http, uri, request, response, **kwargs):
        assert response.status // 100 == 5
        Response.__init__(self, http, uri, request, response, **kwargs)
        Exception.__init__(self, self.reason)


class Resource(object):
    """ A web resource identified by a URI.
    """

    def __init__(self, uri):
        self._uri = URI(uri)

    def __str__(self):
        return "<{0}>".format(str(self._uri))

    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__,
                                 repr(self._uri.string))

    def __eq__(self, other):
        """ Determine equality of two objects based on URI.
        """
        return self._uri == other._uri

    def __ne__(self, other):
        """ Determine inequality of two objects based on URI.
        """
        return self._uri != other._uri

    def __bool__(self):
        return bool(self._uri)

    def __nonzero__(self):
        return bool(self._uri)

    @property
    def __uri__(self):
        return self._uri

    @property
    def uri(self):
        """ The URI of this resource.
        """
        return self._uri

    def resolve(self, reference, strict=True):
        """ Resolve a URI reference against the URI for this resource,
        returning a new resource represented by the new target URI.
        """
        return Resource(self._uri.resolve(reference, strict))

    def get(self, headers=None, redirect_limit=5, **kwargs):
        """ Issue a ``GET`` request to this resource.

        :param headers: headers to be included in the request (optional)
        :type headers: dict
        :param redirect_limit: maximum number of redirects to be handled
            automatically (optional, default=5)
        :param product: name or (name, version) tuple for the client product to
            be listed in the ``User-Agent`` header (optional)
        :param chunk_size: number of bytes to retrieve per chunk (optional,
            default=4096)
        :return: file-like :py:class:`Response <httpstream.http.Response>`
            object from which content can be read
        """
        rq = Request("GET", self._uri, None, headers)
        return rq.submit(redirect_limit=redirect_limit, **kwargs)

    def put(self, body=None, headers=None, **kwargs):
        """ Issue a ``PUT`` request to this resource.
        """
        rq = Request("PUT", self._uri, body, headers)
        return rq.submit(**kwargs)

    def post(self, body=None, headers=None, **kwargs):
        """ Issue a ``POST`` request to this resource.
        """
        rq = Request("POST", self._uri, body, headers)
        return rq.submit(**kwargs)

    def delete(self, headers=None, **kwargs):
        """ Issue a ``DELETE`` request to this resource.
        """
        rq = Request("DELETE", self._uri, None, headers)
        return rq.submit(**kwargs)

    def head(self, headers=None, redirect_limit=5, **kwargs):
        """ Issue a ``HEAD`` request to this resource.
        """
        rq = Request("HEAD", self._uri, None, headers)
        return rq.submit(redirect_limit=redirect_limit, **kwargs)


class ResourceTemplate(object):

    def __init__(self, uri_template):
        if isinstance(uri_template, URITemplate):
            self._uri_template = uri_template
        else:
            self._uri_template = URITemplate(uri_template)

    def __str__(self):
        return "<{0}>".format(str(self._uri_template))

    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__,
                                 repr(self._uri_template.string))

    def __eq__(self, other):
        return self._uri_template == other._uri_template

    def __ne__(self, other):
        return self._uri_template != other._uri_template

    def __bool__(self):
        return bool(self._uri_template)

    def __nonzero__(self):
        return bool(self._uri_template)

    @property
    def uri_template(self):
        """ The URI template string of this resource template.
        """
        return self._uri_template

    def expand(self, **values):
        """ Expand this template into a full URI using the values provided.
        """
        return Resource(self._uri_template.expand(**values))


def get(uri, headers=None, redirect_limit=5, **kwargs):
    return Resource(uri).get(headers, redirect_limit, **kwargs)


def put(uri, body=None, headers=None, **kwargs):
    return Resource(uri).put(body, headers, **kwargs)


def post(uri, body=None, headers=None, **kwargs):
    return Resource(uri).post(body, headers, **kwargs)


def delete(uri, headers=None, **kwargs):
    return Resource(uri).delete(headers, **kwargs)


def head(uri, headers=None, redirect_limit=5, **kwargs):
    return Resource(uri).head(headers, redirect_limit, **kwargs)
