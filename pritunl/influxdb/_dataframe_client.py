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
DataFrame client for InfluxDB
"""
import math

import pandas as pd

from .client import InfluxDBClient


def _pandas_time_unit(time_precision):
    unit = time_precision
    if time_precision == 'm':
        unit = 'ms'
    elif time_precision == 'u':
        unit = 'us'
    elif time_precision == 'n':
        unit = 'ns'
    assert unit in ('s', 'ms', 'us', 'ns')
    return unit


class DataFrameClient(InfluxDBClient):
    """
    The ``DataFrameClient`` object holds information necessary to connect
    to InfluxDB. Requests can be made to InfluxDB directly through the client.
    The client reads and writes from pandas DataFrames.
    """

    EPOCH = pd.Timestamp('1970-01-01 00:00:00.000+00:00')

    def write_points(self, dataframe, measurement, tags=None,
                     time_precision=None, database=None, retention_policy=None,
                     batch_size=None):
        """
        Write to multiple time series names.

        :param dataframe: data points in a DataFrame
        :param measurement: name of measurement
        :param tags: dictionary of tags, with string key-values
        :param time_precision: [Optional, default None] Either 's', 'ms', 'u'
            or 'n'.
        :param batch_size: [Optional] Value to write the points in batches
            instead of all at one time. Useful for when doing data dumps from
            one database to another or when doing a massive write operation
        :type batch_size: int

        """
        if batch_size:
            number_batches = int(math.ceil(
                len(dataframe) / float(batch_size)))
            for batch in range(number_batches):
                start_index = batch * batch_size
                end_index = (batch + 1) * batch_size
                points = self._convert_dataframe_to_json(
                    dataframe.ix[start_index:end_index].copy(),
                    measurement, tags, time_precision
                )
                super(DataFrameClient, self).write_points(
                    points, time_precision, database, retention_policy)
            return True
        else:
            points = self._convert_dataframe_to_json(
                dataframe, measurement, tags, time_precision
            )
            super(DataFrameClient, self).write_points(
                points, time_precision, database, retention_policy)
            return True

    def query(self, query, chunked=False, database=None):
        """
        Quering data into a DataFrame.

        :param chunked: [Optional, default=False] True if the data shall be
            retrieved in chunks, False otherwise.

        """
        results = super(DataFrameClient, self).query(query, database=database)
        if query.upper().startswith("SELECT"):
            if len(results) > 0:
                return self._to_dataframe(results)
            else:
                return {}
        else:
            return results

    def get_list_series(self, database=None):
        """
        Get the list of series, in DataFrame

        """
        results = super(DataFrameClient, self)\
            .query("SHOW SERIES", database=database)
        if len(results):
            return dict(
                (key[0], pd.DataFrame(data)) for key, data in list(results.items())
            )
        else:
            return {}

    def _to_dataframe(self, rs):
        result = {}
        if isinstance(rs, list):
            return list(map(self._to_dataframe, rs))
        for key, data in list(rs.items()):
            name, tags = key
            if tags is None:
                key = name
            else:
                key = (name, tuple(sorted(tags.items())))
            df = pd.DataFrame(data)
            df.time = pd.to_datetime(df.time)
            df.set_index('time', inplace=True)
            df.index = df.index.tz_localize('UTC')
            df.index.name = None
            result[key] = df
        return result

    def _convert_dataframe_to_json(self, dataframe, measurement, tags=None,
                                   time_precision=None):

        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError('Must be DataFrame, but type was: {0}.'
                            .format(type(dataframe)))
        if not (isinstance(dataframe.index, pd.tseries.period.PeriodIndex) or
                isinstance(dataframe.index, pd.tseries.index.DatetimeIndex)):
            raise TypeError('Must be DataFrame with DatetimeIndex or \
                            PeriodIndex.')

        dataframe.index = dataframe.index.to_datetime()
        if dataframe.index.tzinfo is None:
            dataframe.index = dataframe.index.tz_localize('UTC')

        # Convert column to strings
        dataframe.columns = dataframe.columns.astype('str')

        # Convert dtype for json serialization
        dataframe = dataframe.astype('object')

        precision_factor = {
            "n": 1,
            "u": 1e3,
            "ms": 1e6,
            "s": 1e9,
            "m": 1e9 * 60,
            "h": 1e9 * 3600,
        }.get(time_precision, 1)

        points = [
            {'measurement': measurement,
             'tags': tags if tags else {},
             'fields': rec,
             'time': int(ts.value / precision_factor)
             }
            for ts, rec in zip(dataframe.index, dataframe.to_dict('record'))]
        return points

    def _datetime_to_epoch(self, datetime, time_precision='s'):
        seconds = (datetime - self.EPOCH).total_seconds()
        if time_precision == 'h':
            return seconds / 3600
        elif time_precision == 'm':
            return seconds / 60
        elif time_precision == 's':
            return seconds
        elif time_precision == 'ms':
            return seconds * 1e3
        elif time_precision == 'u':
            return seconds * 1e6
        elif time_precision == 'n':
            return seconds * 1e9
