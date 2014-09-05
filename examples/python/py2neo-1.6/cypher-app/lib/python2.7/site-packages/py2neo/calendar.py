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
The `calendar` module provides standardised date management functionality
based on a calendar subgraph::

    from py2neo import neo4j
    from py2neo.calendar import GregorianCalendar

    graph_db = neo4j.GraphDatabaseService()
    time_index = graph_db.get_or_create_index(neo4j.Node, "TIME")
    calendar = GregorianCalendar(time_index)

    graph_db.create(
        {"name": "Alice"},
        (0, "BORN", calendar.day(1800, 1, 1)),
        (0, "DIED", calendar.day(1900, 12, 31)),
    )

The root calendar node is held within a dedicated node index which needs
to be supplied to the calendar constructor.

All dates managed by the :py:class:`GregorianCalendar` class adhere to a
hierarchy such as::

    (CALENDAR)-[:YEAR]->(2000)-[:MONTH]->(12)-[:DAY]->(25)

"""


from __future__ import unicode_literals

from datetime import date as _date

from .neo4j import CypherQuery


class GregorianCalendar(object):

    class Date(object):

        def __init__(self, year, month=None, day=None):
            if year and month and day:
                self._date = _date(year, month, day)
                self._resolution = 3
                self.year = year
                self.month = month
                self.day = day
            elif year and month:
                self._date = _date(year, month, 1)
                self._resolution = 2
                self.year = year
                self.month = month
                self.day = None
            elif year:
                self._date = _date(year, 1, 1)
                self._resolution = 1
                self.year = year
                self.month = None
                self.day = None

        def __str__(self):
            if self.year and self.month and self.day:
                return "{y:04d}-{m:02d}-{d:02d}".format(
                    y=self.year, m=self.month, d=self.day
                )
            elif self.year and self.month:
                return "{y:04d}-{m:02d}".format(
                    y=self.year, m=self.month
                )
            elif self.year:
                return "{y:04d}".format(
                    y=self.year
                )

        def get_node(self, calendar):
            if self.year and self.month and self.day:
                return calendar.day(self.year, self.month, self.day)
            elif self.year and self.month:
                return calendar.month(self.year, self.month)
            elif self.year:
                return calendar.year(self.year)
            else:
                raise ValueError()

    class DateRange(object):

        def __init__(self, start_date=None, end_date=None):
            if start_date and end_date:
                self.start_date = GregorianCalendar.Date(*start_date)
                self.end_date = GregorianCalendar.Date(*end_date)
                # check both dates are compatible
                if self.start_date._resolution != self.end_date._resolution:
                    raise ValueError("Range start and end dates are specified "
                                     "at different resolutions")
                # ensure dates are correctly ordered
                if self.start_date._date > self.end_date._date:
                    self.start_date, self.end_date = self.end_date, self.start_date
            elif start_date:
                self.start_date = GregorianCalendar.Date(*start_date)
                self.end_date = None
            elif end_date:
                self.start_date = None
                self.end_date = GregorianCalendar.Date(*end_date)
            else:
                raise ValueError("Either start date or end date must "
                                 "be specified for a date range")

    def __init__(self, index):
        """ Create a new calendar instance pointed to by the index provided.
        """
        self._index = index
        self._graph_db = self._index.service_root.graph_db
        self._calendar = self._index.get_or_create("calendar", "Gregorian", {})

    def calendar(self):
        return self._calendar

    def day(self, year, month, day):
        """ Fetch the calendar node representing the day specified by `year`,
        `month` and `day`.
        """
        d = GregorianCalendar.Date(year, month, day)
        date_path = self._calendar.get_or_create_path(
            "YEAR",  {"year": d.year},
            "MONTH", {"year": d.year, "month": d.month},
            "DAY",   {"year": d.year, "month": d.month, "day": d.day},
        )
        return date_path.nodes[-1]

    def month(self, year, month):
        """ Fetch the calendar node representing the month specified by `year`
        and `month`.
        """
        d = GregorianCalendar.Date(year, month)
        date_path = self._calendar.get_or_create_path(
            "YEAR",  {"year": d.year},
            "MONTH", {"year": d.year, "month": d.month},
        )
        return date_path.nodes[-1]

    def year(self, year):
        """ Fetch the calendar node representing the year specified by `year`.
        """
        d = GregorianCalendar.Date(year)
        date_path = self._calendar.get_or_create_path(
            "YEAR",  {"year": d.year},
        )
        return date_path.nodes[-1]

    def date(self, date):
        return GregorianCalendar.Date(*date).get_node(self)

    def date_range(self, start_date=None, end_date=None):
        """ Fetch the calendar node representing the date range defined by
        `start_date` and `end_date`. If either are unspecified, this defines an
        open-ended range. Either `start_date` or `end_date` must be specified.
        """
        #                         (CAL)
        #                           |
        #                       [:RANGE]
        #                           |
        #                           v
        # (START)<-[:START_DATE]-(RANGE)-[:END_DATE]->(END)
        range_ = GregorianCalendar.DateRange(start_date, end_date)
        start, end = range_.start_date, range_.end_date
        if start and end:
            # if start and end are equal, return the day node instead
            if (start.year, start.month, start.day) == (end.year, end.month, end.day):
                return start.get_node(self)
            if (start.year, start.month) == (end.year, end.month):
                root = self.month(start.year, start.month)
            elif start.year == end.year:
                root = self.year(start.year)
            else:
                root = self._calendar
            query = """\
                START z=node({z}), s=node({s}), e=node({e})
                CREATE UNIQUE (s)<-[:START_DATE]-(r {r})-[:END_DATE]->(e),
                              (z)-[:DATE_RANGE]->(r {r})
                RETURN r
            """
            params = {
                "z": root._id,
                "s": start.get_node(self)._id,
                "e": end.get_node(self)._id,
                "r": {
                    "start_date": str(start),
                    "end_date": str(end),
                },
            }
        elif start:
            query = """\
                START z=node({z}), s=node({s})
                CREATE UNIQUE (s)<-[:START_DATE]-(r {r}),
                              (z)-[:DATE_RANGE]->(r {r})
                RETURN r
            """
            params = {
                "z": self._calendar._id,
                "s": start.get_node(self)._id,
                "r": {
                    "start_date": str(start),
                },
            }
        elif end:
            query = """\
                START z=node({z}), e=node({e})
                CREATE UNIQUE (r {r})-[:END_DATE]->(e),
                              (z)-[:DATE_RANGE]->(r {r})
                RETURN r
            """
            params = {
                "z": self._calendar._id,
                "e": end.get_node(self)._id,
                "r": {
                    "end_date": str(end),
                },
            }
        else:
            raise ValueError("Either start or end date must be supplied "
                             "for a date range")
        return CypherQuery(self._graph_db, query).execute_one(**params)

    def quarter(self, year, quarter):
        if quarter == 1:
            return self.date_range((year, 1, 1), (year, 3, 31))
        elif quarter == 2:
            return self.date_range((year, 4, 1), (year, 6, 30))
        elif quarter == 3:
            return self.date_range((year, 7, 1), (year, 9, 30))
        elif quarter == 4:
            return self.date_range((year, 10, 1), (year, 12, 31))
        else:
            raise ValueError("quarter must be in 1..4")
