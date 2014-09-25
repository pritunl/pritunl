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

    def add_period(self, timestamp, cpu_usage, mem_usage):
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

    def get_period(self, period):
        date_end = self._get_period_timestamp(
            period, datetime.datetime.utcnow())

        if period == '1m':
            date_start = date_end - datetime.timedelta(hours=6)
            date_step = datetime.timedelta(minutes=1)
        elif period == '5m':
            date_start = date_end - datetime.timedelta(days=1)
            date_step = datetime.timedelta(minutes=5)
        elif period == '30m':
            date_start = date_end - datetime.timedelta(days=7)
            date_step = datetime.timedelta(minutes=30)
        elif period == '2h':
            date_start = date_end - datetime.timedelta(days=30)
            date_step = datetime.timedelta(hours=2)
        elif period == '1d':
            date_start = date_end - datetime.timedelta(days=365)
            date_step = datetime.timedelta(days=1)
        date_cur = date_start

        data = {
            'cpu_usage': [],
            'mem_usage': [],
        }

        results = self.collection.aggregate([
            {'$match': {
                'host_id': self.host_id,
                'period': period,
            }},
            {'$project': {
                'timestamp': True,
                'cpu_usage': {'$divide': ['$cpu_usage', '$count']},
                'mem_usage': {'$divide': ['$mem_usage', '$count']},
            }},
            {'$sort': {
                'timestamp': pymongo.ASCENDING,
            }}
        ])['result']

        for doc in results:
            if date_cur > doc['timestamp']:
                continue

            while date_cur < doc['timestamp']:
                timestamp = int(date_cur.strftime('%s'))
                data['cpu_usage'].append((timestamp, 0))
                data['mem_usage'].append((timestamp, 0))
                date_cur += date_step

            timestamp = int(doc['timestamp'].strftime('%s'))
            data['cpu_usage'].append((timestamp, doc['cpu_usage']))
            data['mem_usage'].append((timestamp, doc['mem_usage']))

        while date_cur <= date_end:
            timestamp = int(date_cur.strftime('%s'))
            data['cpu_usage'].append((timestamp, 0))
            data['mem_usage'].append((timestamp, 0))
            date_cur += date_step

        return data
