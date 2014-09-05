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

"""
Utility module
"""


from __future__ import unicode_literals

from itertools import cycle, islice
import re
import warnings


__all__ = ["numberise", "compact", "flatten", "round_robin", "deprecated",
           "version_tuple", "is_collection", "has_all", "ustr", "pendulate",
           "Record", "RecordProducer"]


def numberise(n):
    """ Convert a value to an integer if possible. If not, simply return
        the input value.
    """
    if n == "NaN":
        return None
    try:
        return int(n)
    except ValueError:
        return n


def compact(obj):
    """ Return a copy of an object with all :py:const:`None` values removed.
    """
    if isinstance(obj, dict):
        return dict((key, value) for key, value in obj.items() if value is not None)
    else:
        return obj.__class__(value for value in obj if value is not None)


def flatten(*values):
    for value in values:
        if hasattr(value, "__iter__"):
            for val in value:
                yield val
        else:
            yield value


def round_robin(*iterables):
    """ Cycle through a number of iterables, returning
        the next item from each in turn.

        round_robin('ABC', 'D', 'EF') --> A D E B F C

        Original recipe credited to George Sakkis
        Python 2/3 cross-compatibility tweak by Nigel Small
    """
    pending = len(iterables)
    nexts = cycle(iter(it) for it in iterables)
    while pending:
        try:
            for n in nexts:
                yield next(n)
        except StopIteration:
            pending -= 1
            nexts = cycle(islice(nexts, pending))


def deprecated(message):
    """ Decorator for deprecating functions and methods.

    ::

        @deprecated("'foo' has been deprecated in favour of 'bar'")
        def foo(x):
            pass

    """
    def f__(f):
        def f_(*args, **kwargs):
            warnings.warn(message, category=DeprecationWarning, stacklevel=2)
            return f(*args, **kwargs)
        f_.__name__ = f.__name__
        f_.__doc__ = f.__doc__
        f_.__dict__.update(f.__dict__)
        return f_
    return f__


VERSION = re.compile("(\d+\.\d+(\.\d+)?)")


def version_tuple(string):
    numbers = VERSION.match(string)
    if numbers:
        version = [int(n) for n in numbers.group(0).split(".")]
        extra = string[len(numbers.group(0)):]
        while extra.startswith(".") or extra.startswith("-"):
            extra = extra[1:]
    else:
        version = []
        extra = string
    while len(version) < 3:
        version += [0]
    version += [extra]
    return tuple(version)


def is_collection(obj):
    """ Returns true for any iterable which is not a string or byte sequence.
    """
    try:
        if isinstance(obj, unicode):
            return False
    except NameError:
        pass
    if isinstance(obj, bytes):
        return False
    try:
        iter(obj)
    except TypeError:
        return False
    try:
        hasattr(None, obj)
    except TypeError:
        return True
    return False


has_all = lambda iterable, items: all(item in iterable for item in items)


try:
    unicode
except NameError:
    # Python 3
    def ustr(s, encoding="utf-8"):
        if isinstance(s, str):
            return s
        try:
            return s.decode(encoding)
        except AttributeError:
            return str(s)
else:
    # Python 2
    def ustr(s, encoding="utf-8"):
        if isinstance(s, str):
            return s.decode(encoding)
        else:
            return unicode(s)


def pendulate(collection):
    count = len(collection)
    for i in range(count):
        if i % 2 == 0:
            index = i // 2
        else:
            index = count - ((i + 1) // 2)
        yield index, collection[index]


class Record(object):
    """ A single row of a Cypher execution result, holding a sequence of named
    values.
    """

    def __init__(self, producer, values):
        self._producer = producer
        self._values = tuple(values)
    
    def __repr__(self):
        return "Record(columns={0}, values={1})".format(self._producer.columns, self._values)
        
    def __getattr__(self, attr):
        return self._values[self._producer.column_indexes[attr]]
        
    def __getitem__(self, item):
        if isinstance(item, (int, slice)):
            return self._values[item]
        else:
            return self._values[self._producer.column_indexes[item]]

    def __len__(self):
        return len(self._producer.columns)

    @property
    def columns(self):
        """ The column names defined for this record.

        :return: tuple of column names
        """
        return self._producer.columns

    @property
    def values(self):
        """ The values stored in this record.

        :return: tuple of values
        """
        return self._values


class RecordProducer(object):

    def __init__(self, columns):
        self._columns = tuple(columns)
        self._column_indexes = dict((b, a) for a, b in enumerate(columns))

    def __repr__(self):
        return "RecordProducer(columns={0})".format(self._columns)

    @property
    def columns(self):
        return self._columns

    @property
    def column_indexes(self):
        return self._column_indexes

    def produce(self, values):
        """ Produce a record from a set of values.
        """
        return Record(self, values)
