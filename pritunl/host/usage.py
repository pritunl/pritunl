from pritunl.host import usage_utils

from pritunl.helpers import *
from pritunl import settings
from pritunl import mongo
from pritunl import utils

import pymongo
import os
import json
import random
import datetime

class HostUsage(object):
    def __init__(self, host_id):
        self.host_id = host_id

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('hosts_usage')

    def add_period(self, timestamp, cpu_usage, mem_usage):
        cpu_usage = round(cpu_usage, 4)
        mem_usage = round(mem_usage, 4)

        bulk = self.collection.initialize_unordered_bulk_op()

        for period in ('1m', '5m', '30m', '2h', '1d'):
            spec = {
                'host_id': self.host_id,
                'period': period,
                'timestamp': usage_utils.get_period_timestamp(
                    period, timestamp),
            }
            doc = {'$inc': {
                'count': 1,
                'cpu': cpu_usage,
                'mem': mem_usage,
            }}
            rem_spec = {
                'host_id': self.host_id,
                'period': period,
                'timestamp': {
                    '$lt': usage_utils.get_period_max_timestamp(
                        period, timestamp),
                },
            }

            bulk.find(spec).upsert().update(doc)
            bulk.find(rem_spec).remove()

        bulk.execute()

    def get_period(self, period):
        date_end = usage_utils.get_period_timestamp(period, utils.now())

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
            'cpu': [],
            'mem': [],
        }

        results = self.collection.aggregate([
            {'$match': {
                'host_id': self.host_id,
                'period': period,
            }},
            {'$project': {
                'timestamp': True,
                'cpu': {'$divide': ['$cpu', '$count']},
                'mem': {'$divide': ['$mem', '$count']},
            }},
            {'$sort': {
                'timestamp': pymongo.ASCENDING,
            }}
        ])

        for doc in results:
            if date_cur > doc['timestamp']:
                continue

            while date_cur < doc['timestamp']:
                timestamp = int(date_cur.strftime('%s'))
                data['cpu'].append((timestamp, 0))
                data['mem'].append((timestamp, 0))
                date_cur += date_step

            timestamp = int(doc['timestamp'].strftime('%s'))
            data['cpu'].append((timestamp, doc['cpu']))
            data['mem'].append((timestamp, doc['mem']))
            date_cur += date_step

        while date_cur <= date_end:
            timestamp = int(date_cur.strftime('%s'))
            data['cpu'].append((timestamp, 0))
            data['mem'].append((timestamp, 0))
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
        elif period == '5m':
            date_end = date - datetime.timedelta(minutes=date.minute % 5)
            date_cur = date_end - datetime.timedelta(days=1)
            date_step = datetime.timedelta(minutes=5)
        elif period == '30m':
            date_end = date - datetime.timedelta(minutes=date.minute % 30)
            date_cur = date_end - datetime.timedelta(days=7)
            date_step = datetime.timedelta(minutes=30)
        elif period == '2h':
            date_end = date - datetime.timedelta(minutes=date.minute,
                hours=date.hour % 2)
            date_cur = date_end - datetime.timedelta(days=30)
            date_step = datetime.timedelta(hours=2)
        elif period == '1d':
            date_end = date - datetime.timedelta(minutes=date.minute,
                hours=date.hour)
            date_cur = date_end - datetime.timedelta(days=365)
            date_step = datetime.timedelta(days=1)

        cpu = 0.3
        mem = 0.3
        def usage_rand(x):
            x += random.uniform(-0.01, 0.01)
            x = max(x, 0.25)
            x = min(x, 0.35)
            return x

        data = {
            'cpu': [],
            'mem': [],
        }

        while date_cur < date_end:
            date_cur += date_step

            timestamp = int(date_cur.strftime('%s'))
            cpu = usage_rand(cpu)
            mem = usage_rand(mem)

            data['cpu'].append((timestamp, cpu))
            data['mem'].append((timestamp, mem))

        return data

    def write_periods_random(self):
        data = {}
        for period in ('1m', '5m', '30m', '2h', '1d'):
            data[period] = self.get_period_random(period)

        path = os.path.join(settings.conf.temp_path, 'demo_usage')
        with open(path, 'w') as demo_file:
            demo_file.write(json.dumps(data))
        return data
