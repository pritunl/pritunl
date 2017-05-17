from pritunl.helpers import *
from pritunl import settings
from pritunl import mongo
from pritunl import utils

import os
import json
import random
import datetime

class ServerBandwidth(object):
    def __init__(self, server_id):
        self.server_id = server_id

    @cached_static_property
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

    def add_data(self, timestamp, received, sent):
        bulk = self.collection.initialize_unordered_bulk_op()

        for period in ('1m', '5m', '30m', '2h', '1d'):
            spec = {
                'server_id': self.server_id,
                'period': period,
                'timestamp': self._get_period_timestamp(period, timestamp),
            }
            doc = {'$inc': {
                'received': received,
                'sent': sent,
            }}
            rem_spec = {
                'server_id': self.server_id,
                'period': period,
                'timestamp': {
                    '$lt': self._get_period_max_timestamp(period, timestamp),
                },
            }

            bulk.find(spec).upsert().update(doc)
            bulk.find(rem_spec).remove()

        bulk.execute()

    def get_period(self, period):
        date_end = self._get_period_timestamp(period, utils.now())

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
        project = {
            'timestamp': True,
            'received': True,
            'sent': True,
        }

        for doc in self.collection.find(spec, project).sort('timestamp'):
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
            date_cur += date_step

        while date_cur <= date_end:
            timestamp = int(date_cur.strftime('%s'))
            data['received'].append((timestamp, 0))
            data['sent'].append((timestamp, 0))
            date_cur += date_step

        return data

    def get_period_random(self, period):
        date = utils.now()
        date -= datetime.timedelta(microseconds=date.microsecond,
            seconds=date.second)

        if period == '1m':
            date_end = date
            date_cur = date_end - datetime.timedelta(hours=6)
            date_step = datetime.timedelta(minutes=1)
            bytes_recv = 700000
            bytes_sent = 700000
            bytes_step = 50000
            bytes_min = 500000
            bytes_max = 900000
        elif period == '5m':
            date_end = date - datetime.timedelta(minutes=date.minute % 5)
            date_cur = date_end - datetime.timedelta(days=1)
            date_step = datetime.timedelta(minutes=5)
            bytes_recv = 3500000
            bytes_sent = 3500000
            bytes_step = 250000
            bytes_min = 3000000
            bytes_max = 4000000
        elif period == '30m':
            date_end = date - datetime.timedelta(minutes=date.minute % 30)
            date_cur = date_end - datetime.timedelta(days=7)
            date_step = datetime.timedelta(minutes=30)
            bytes_recv = 21000000
            bytes_sent = 21000000
            bytes_step = 2000000
            bytes_min = 17000000
            bytes_max = 25000000
        elif period == '2h':
            date_end = date - datetime.timedelta(minutes=date.minute,
                hours=date.hour % 2)
            date_cur = date_end - datetime.timedelta(days=30)
            date_step = datetime.timedelta(hours=2)
            bytes_recv = 84000000
            bytes_sent = 84000000
            bytes_step = 2000000
            bytes_min = 78000000
            bytes_max = 90000000
        elif period == '1d':
            date_end = date - datetime.timedelta(minutes=date.minute,
                hours=date.hour)
            date_cur = date_end - datetime.timedelta(days=365)
            date_step = datetime.timedelta(days=1)
            bytes_recv = 1008000000
            bytes_sent = 1008000000
            bytes_step = 10000000
            bytes_min = 208000000
            bytes_max = 1808000000

        def bandwidth_rand(x):
            x += random.uniform(-bytes_step, bytes_step)
            x = max(x, bytes_min)
            x = min(x, bytes_max)
            return x

        data = {
            'received': [],
            'received_total': 0,
            'sent': [],
            'sent_total': 0,
        }

        while date_cur < date_end:
            date_cur += date_step

            timestamp = int(date_cur.strftime('%s'))
            bytes_recv = bandwidth_rand(bytes_recv)
            bytes_sent = bandwidth_rand(bytes_sent)

            data['received'].append((timestamp, bytes_recv))
            data['received_total'] += bytes_recv
            data['sent'].append((timestamp, bytes_sent))
            data['sent_total'] += bytes_sent

        return data

    def write_periods_random(self):
        data = {}
        for period in ('1m', '5m', '30m', '2h', '1d'):
            data[period] = self.get_period_random(period)

        path = os.path.join(settings.conf.temp_path, 'demo_bandwidth')
        with open(path, 'w') as demo_file:
            demo_file.write(json.dumps(data))
        return data
