# -*- coding: utf-8 -*-
# pylama:ignore=E0602,W0612
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

__all__ = ['DataFrameClient']

try:
    import pandas
    del pandas
except ImportError as err:  # FIXME W0612 local variable 'err' is assigned to but never used [pyflakes] - Possibly related to below FIXME
    from .client import InfluxDBClient

    class DataFrameClient(InfluxDBClient):
        def __init__(self, *a, **kw):
            raise ImportError("DataFrameClient requires Pandas "
                              "which couldn't be imported: %s" % err)  # FIXME E0602 undefined name 'err' [pyflakes]
else:
    from ._dataframe_client import DataFrameClient
