from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
import pritunl.mongo as mongo
import pymongo

class HostUsage(object):
    def __init__(self, host_id):
        self.host_id = host_id

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('hosts_usage')

    def _get_period_timestamp(self, period, timestamp):
        timestamp -= datetime.timedelta(microseconds=timestamp.microsecond,
                seconds=timestamp.second)

        if period == '1m':
            return timestamp
        elif period == '5m':
            return timestamp - datetime.timedelta(
                minutes=timestamp.minute % 5)
        elif period == '30m':
            return timestamp - datetime.timedelta(
                minutes=timestamp.minute % 30)
        elif period == '2h':
            return timestamp - datetime.timedelta(
                hours=timestamp.hour % 2, minutes=timestamp.minute)
        elif period == '1d':
            return timestamp - datetime.timedelta(
                hours=timestamp.hour, minutes=timestamp.minute)

    def _get_period_max_timestamp(self, period, timestamp):
        timestamp -= datetime.timedelta(microseconds=timestamp.microsecond,
                seconds=timestamp.second)

        if period == '1m':
            return timestamp - datetime.timedelta(hours=6)
        elif period == '5m':
            return timestamp - datetime.timedelta(
                minutes=timestamp.minute % 5) - datetime.timedelta(days=1)
        elif period == '30m':
            return timestamp - datetime.timedelta(
                minutes=timestamp.minute % 30) - datetime.timedelta(days=7)
        elif period == '2h':
            return timestamp - datetime.timedelta(
                hours=timestamp.hour % 2,
                minutes=timestamp.minute) - datetime.timedelta(days=30)
        elif period == '1d':
            return timestamp - datetime.timedelta(
                hours=timestamp.hour,
                minutes=timestamp.minute) - datetime.timedelta(days=365)

    def add_usage(self, timestamp, cpu_usage, mem_usage):
        bulk = self.collection.initialize_unordered_bulk_op()

        for period in ('1m', '5m', '30m', '2h', '1d'):
            bulk.find({
                'host_id': self.host_id,
                'period': period,
                'timestamp': self._get_period_timestamp(period, timestamp),
            }).upsert().update({'$inc': {
                'count': 1,
                'cpu_usage': cpu_usage,
                'mem_usage': mem_usage,
            }})

        for period in ('1m', '5m', '30m', '2h', '1d'):
            bulk.find({
                'host_id': self.host_id,
                'period': period,
                'timestamp': {
                    '$lt': self._get_period_max_timestamp(period, timestamp),
                },
            }).remove()

        bulk.execute()
