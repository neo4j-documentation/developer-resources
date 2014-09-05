#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2011-2014, Nigel Small
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

from .packages.jsonstream import assembled


__all__ = ["IndexTypeError", "ServerException", "ClientError", "ServerError",
           "CypherError", "BatchError"]


class IndexTypeError(TypeError):
    pass


class ServerException(object):

    def __init__(self, data):
        self._message = data.get("message")
        self._exception = data.get("exception")
        self._full_name = data.get("fullname")
        self._stack_trace = data.get("stacktrace")
        try:
            self._cause = ServerException(data["cause"])
        except KeyError:
            self._cause = None

    @property
    def message(self):
        return self._message

    @property
    def exception(self):
        return self._exception

    @property
    def full_name(self):
        return self._full_name

    @property
    def stack_trace(self):
        return self._stack_trace

    @property
    def cause(self):
        return self._cause


class ClientError(Exception):

    def __init__(self, response):
        assert response.status_code // 100 == 4
        try:
            self.__cause__ = response
        except TypeError:
            pass
        if response.is_json:
            self._server_exception = ServerException(assembled(response))
            Exception.__init__(self, self._server_exception.message)
        else:
            self._server_exception = None
            Exception.__init__(self, response.args[0])

    def __getattr__(self, item):
        try:
            return getattr(self._server_exception, item)
        except AttributeError:
            return getattr(self.__cause__, item)


class ServerError(Exception):

    def __init__(self, response):
        assert response.status_code // 100 == 5
        try:
            self.__cause__ = response
        except TypeError:
            pass
        # TODO: check for unhandled HTML errors (on 500)
        if response.is_json:
            self._server_exception = ServerException(assembled(response))
            Exception.__init__(self, self._server_exception.message)
        else:
            self._server_exception = None
            Exception.__init__(self, response.args[0])

    def __getattr__(self, item):
        try:
            return getattr(self._server_exception, item)
        except AttributeError:
            return getattr(self.__cause__, item)


class _FeatureError(Exception):

    def __init__(self, response):
        self._response = response
        Exception.__init__(self, self.message)

    @property
    def message(self):
        return self._response.message

    @property
    def exception(self):
        return self._response.exception

    @property
    def full_name(self):
        return self._response.full_name

    @property
    def stack_trace(self):
        return self._response.stack_trace

    @property
    def cause(self):
        return self._response.cause

    @property
    def request(self):
        return self._response.request

    @property
    def response(self):
        return self._response


class CypherError(_FeatureError):

    pass


class BatchError(_FeatureError):

    pass
