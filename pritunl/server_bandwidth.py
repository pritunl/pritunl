from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
import pritunl.mongo as mongo
import time
import pymongo

class ServerBandwidth:
    def __init__(self, server_id):
        self.server_id = server_id

    @static_property
    def collection(cls):
        return mongo.get_collection('servers_bandwidth')

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

    def add_bandwidth(self, timestamp, received, sent):
        bulk = self.collection.initialize_unordered_bulk_op()

        for period in ('1m', '5m', '30m', '2h', '1d'):
            bulk.find({
                'server_id': self.server_id,
                'period': period,
                'timestamp': self._get_period_timestamp(period, timestamp),
            }).upsert().update({'$inc': {
                'received': received,
                'sent': sent,
            }})

        for period in ('1m', '5m', '30m', '2h', '1d'):
            bulk.find({
                'server_id': self.server_id,
                'period': period,
                'timestamp': {
                    '$lt': self._get_period_max_timestamp(period, timestamp),
                },
            }).remove()

        bulk.execute()

    def get_bandwidth(self, period):
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
            'received': [],
            'received_total': 0,
            'sent': [],
            'sent_total': 0,
        }

        spec = {
            'server_id': self.server_id,
            'period': period,
        }

        for doc in self.collection.find(spec).sort('timestamp'):
            if date_cur > doc['timestamp']:
                continue
            while date_cur < doc['timestamp']:
                timestamp = int(date_cur.strftime('%s'))
                data['received'].append((timestamp, 0))
                data['sent'].append((timestamp, 0))
                date_cur += date_step
            timestamp = int(doc['timestamp'].strftime('%s'))
            received = doc['received']
            sent = doc['sent']
            data['received'].append((timestamp, received))
            data['sent'].append((timestamp, sent))
            data['received_total'] += received
            data['sent_total'] += sent

        while date_cur <= date_end:
            timestamp = int(date_cur.strftime('%s'))
            data['received'].append((timestamp, 0))
            data['sent'].append((timestamp, 0))
            date_cur += date_step

        return data

    def get_time_block(self, timestamp):
        spec = {
            'server_id': self.server_id,
            'timestamp': timestamp,
        }
        time_block = cls(spec=spec)
        if not time_block:
            time_block = cls()
