# -*- coding: utf-8 -*-
# The MIT License (MIT)
# 
# Copyright (c) 2013 InfluxDB
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Helper class for InfluxDB
"""
from collections import namedtuple, defaultdict
from datetime import datetime
from warnings import warn

import six


class SeriesHelper(object):

    """
    Subclassing this helper eases writing data points in bulk.
    All data points are immutable, insuring they do not get overwritten.
    Each subclass can write to its own database.
    The time series names can also be based on one or more defined fields.
    The field "time" can be specified when creating a point, and may be any of
    the time types supported by the client (i.e. str, datetime, int).
    If the time is not specified, the current system time (utc) will be used.

    Annotated example::

        class MySeriesHelper(SeriesHelper):
            class Meta:
                # Meta class stores time series helper configuration.
                series_name = 'events.stats.{server_name}'
                # Series name must be a string, curly brackets for dynamic use.
                fields = ['time', 'server_name']
                # Defines all the fields in this time series.
                ### Following attributes are optional. ###
                client = TestSeriesHelper.client
                # Client should be an instance of InfluxDBClient.
                :warning: Only used if autocommit is True.
                bulk_size = 5
                # Defines the number of data points to write simultaneously.
                # Only applicable if autocommit is True.
                autocommit = True
                # If True and no bulk_size, then will set bulk_size to 1.

    """
    __initialized__ = False

    def __new__(cls, *args, **kwargs):
        """
        Initializes class attributes for subsequent constructor calls.

        :note: *args and **kwargs are not explicitly used in this function,
        but needed for Python 2 compatibility.
        """
        if not cls.__initialized__:
            cls.__initialized__ = True
            try:
                _meta = getattr(cls, 'Meta')
            except AttributeError:
                raise AttributeError(
                    'Missing Meta class in {0}.'.format(
                        cls.__name__))

            for attr in ['series_name', 'fields', 'tags']:
                try:
                    setattr(cls, '_' + attr, getattr(_meta, attr))
                except AttributeError:
                    raise AttributeError(
                        'Missing {0} in {1} Meta class.'.format(
                            attr,
                            cls.__name__))

            cls._autocommit = getattr(_meta, 'autocommit', False)

            cls._client = getattr(_meta, 'client', None)
            if cls._autocommit and not cls._client:
                raise AttributeError(
                    'In {0}, autocommit is set to True, but no client is set.'
                    .format(cls.__name__))

            try:
                cls._bulk_size = getattr(_meta, 'bulk_size')
                if cls._bulk_size < 1 and cls._autocommit:
                    warn(
                        'Definition of bulk_size in {0} forced to 1, '
                        'was less than 1.'.format(cls.__name__))
                    cls._bulk_size = 1
            except AttributeError:
                cls._bulk_size = -1
            else:
                if not cls._autocommit:
                    warn(
                        'Definition of bulk_size in {0} has no affect because'
                        ' autocommit is false.'.format(cls.__name__))

            cls._datapoints = defaultdict(list)

            if 'time' in cls._fields:
                cls._fields.remove('time')
            cls._type = namedtuple(cls.__name__,
                                   cls._fields + cls._tags + ['time'])
        return super(SeriesHelper, cls).__new__(cls)

    def __init__(self, **kw):
        """
        Constructor call creates a new data point. All fields must be present.

        :note: Data points written when `bulk_size` is reached per Helper.
        :warning: Data points are *immutable* (`namedtuples`).
        """
        cls = self.__class__
        timestamp = kw.pop('time', self._current_timestamp())

        if sorted(cls._fields + cls._tags) != sorted(kw.keys()):
            raise NameError(
                'Expected {0}, got {1}.'.format(
                    sorted(cls._fields + cls._tags),
                    list(kw.keys())))

        cls._datapoints[cls._series_name.format(**kw)].append(
            cls._type(time=timestamp, **kw)
        )

        if cls._autocommit and \
                sum(len(series) for series in list(cls._datapoints.values())) \
                >= cls._bulk_size:
            cls.commit()

    @classmethod
    def commit(cls, client=None):
        """
        Commit everything from datapoints via the client.

        :param client: InfluxDBClient instance for writing points to InfluxDB.
        :attention: any provided client will supersede the class client.
        :return: result of client.write_points.
        """
        if not client:
            client = cls._client
        rtn = client.write_points(cls._json_body_())
        cls._reset_()
        return rtn

    @classmethod
    def _json_body_(cls):
        """
        :return: JSON body of these datapoints.
        """
        json = []
        for series_name, data in six.iteritems(cls._datapoints):
            for point in data:
                json_point = {
                    "measurement": series_name,
                    "fields": {},
                    "tags": {},
                    "time": getattr(point, "time")
                }

                for field in cls._fields:
                    json_point['fields'][field] = getattr(point, field)

                for tag in cls._tags:
                    json_point['tags'][tag] = getattr(point, tag)

                json.append(json_point)
        return json

    @classmethod
    def _reset_(cls):
        """
        Reset data storage.
        """
        cls._datapoints = defaultdict(list)

    def _current_timestamp(self):
        return datetime.utcnow()
