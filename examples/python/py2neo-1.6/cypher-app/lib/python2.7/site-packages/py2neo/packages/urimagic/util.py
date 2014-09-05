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
