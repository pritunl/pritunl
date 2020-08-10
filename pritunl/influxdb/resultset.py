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

import warnings

from .exceptions import InfluxDBClientError

_sentinel = object()


class ResultSet(object):
    """A wrapper around a single InfluxDB query result"""

    def __init__(self, series, raise_errors=True):
        self._raw = series
        self._error = self.raw.get('error', None)

        if self.error is not None and raise_errors is True:
            raise InfluxDBClientError(self.error)

    @property
    def raw(self):
        """Raw JSON from InfluxDB"""
        return self._raw

    @raw.setter
    def raw(self, value):
        self._raw = value

    @property
    def error(self):
        """Error returned by InfluxDB"""
        return self._error

    def __getitem__(self, key):
        """
        :param key: Either a serie name, or a tags_dict, or
                    a 2-tuple(serie_name, tags_dict).
                    If the serie name is None (or not given) then any serie
                    matching the eventual given tags will be given its points
                    one after the other.
                    To get the points of every serie in this resultset then
                    you have to provide None as key.
        :return: A generator yielding `Point`s matching the given key.
        NB:
        The order in which the points are yielded is actually undefined but
        it might change..
        """

        warnings.warn(
            ("ResultSet's ``__getitem__`` method will be deprecated. Use"
             "``get_points`` instead."),
            DeprecationWarning
        )

        if isinstance(key, tuple):
            if 2 != len(key):
                raise TypeError('only 2-tuples allowed')
            name = key[0]
            tags = key[1]
            if not isinstance(tags, dict) and tags is not None:
                raise TypeError('tags should be a dict')
        elif isinstance(key, dict):
            name = None
            tags = key
        else:
            name = key
            tags = None

        return self.get_points(name, tags)

    def get_points(self, measurement=None, tags=None):
        """
        Returns a generator for all the points that match the given filters.

        :param measurement: The measurement name
        :type measurement: str

        :param tags: Tags to look for
        :type tags: dict

        :return: Points generator
        """

        # Raise error if measurement is not str or bytes
        if not isinstance(measurement,
                          (bytes, type(b''.decode()), type(None))):
            raise TypeError('measurement must be an str or None')

        for serie in self._get_series():
            serie_name = serie.get('measurement', serie.get('name', 'results'))
            if serie_name is None:
                # this is a "system" query or a query which
                # doesn't return a name attribute.
                # like 'show retention policies' ..
                if tags is None:
                    for item in self._get_points_for_serie(serie):
                        yield item

            elif measurement in (None, serie_name):
                # by default if no tags was provided then
                # we will matches every returned serie
                serie_tags = serie.get('tags', {})
                if tags is None or self._tag_matches(serie_tags, tags):
                    for item in self._get_points_for_serie(serie):
                        yield item

    def __repr__(self):
        items = []

        for item in list(self.items()):
            items.append("'%s': %s" % (item[0], list(item[1])))

        return "ResultSet({%s})" % ", ".join(items)

    def __iter__(self):
        """ Iterating a ResultSet will yield one dict instance per serie result.
        """
        for key in list(self.keys()):
            yield list(self.__getitem__(key))

    def _tag_matches(self, tags, filter):
        """Checks if all key/values in filter match in tags"""
        for tag_name, tag_value in list(filter.items()):
            # using _sentinel as I'm not sure that "None"
            # could be used, because it could be a valid
            # serie_tags value : when a serie has no such tag
            # then I think it's set to /null/None/.. TBC..
            serie_tag_value = tags.get(tag_name, _sentinel)
            if serie_tag_value != tag_value:
                return False
        return True

    def _get_series(self):
        """Returns all series"""
        return self.raw.get('series', [])

    def __len__(self):
        return len(list(self.keys()))

    def keys(self):
        """
        :return: List of keys. Keys are tuples (serie_name, tags)
        """
        keys = []
        for serie in self._get_series():
            keys.append(
                (serie.get('measurement',
                           serie.get('name', 'results')),
                 serie.get('tags', None))
            )
        return keys

    def items(self):
        """
        :return: List of tuples, (key, generator)
        """
        items = []
        for serie in self._get_series():
            serie_key = (serie.get('measurement',
                                   serie.get('name', 'results')),
                         serie.get('tags', None))
            items.append(
                (serie_key, self._get_points_for_serie(serie))
            )
        return items

    def _get_points_for_serie(self, serie):
        """ Return generator of dict from columns and values of a serie

        :param serie: One serie
        :return: Generator of dicts
        """
        for point in serie.get('values', []):
            yield self.point_from_cols_vals(
                serie['columns'],
                point
            )

    @staticmethod
    def point_from_cols_vals(cols, vals):
        """ Creates a dict from columns and values lists

        :param cols: List of columns
        :param vals: List of values
        :return: Dict where keys are columns.
        """
        point = {}
        for col_index, col_name in enumerate(cols):
            point[col_name] = vals[col_index]
        return point
