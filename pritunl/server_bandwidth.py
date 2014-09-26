from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
import pritunl.mongo as mongo

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

        while date_cur <= date_end:
            timestamp = int(date_cur.strftime('%s'))
            data['received'].append((timestamp, 0))
            data['sent'].append((timestamp, 0))
            date_cur += date_step

        return data

    def get_period_random(self, period):
        # Generate random bandwidth data for demo and write to file
        import json
        import random
        data = {}
        date = datetime.datetime.utcnow()
        date -= datetime.timedelta(microseconds=date.microsecond,
            seconds=date.second)
        periods = (period,) if period else ('1m', '5m', '30m', '2h', '1d')

        for period in periods:
            if period == '1m':
                date_end = date
                date_cur = date_end - datetime.timedelta(hours=6)
                date_step = datetime.timedelta(minutes=1)
                bytes_recv = 700000
                bytes_sent = 700000
                bandwidth_rand = lambda x: random.randint(
                    max(x - 50000, 0), max(x + 50000, 0))
            elif period == '5m':
                date_end = date - datetime.timedelta(minutes=date.minute % 5)
                date_cur = date_end - datetime.timedelta(days=1)
                date_step = datetime.timedelta(minutes=5)
                bytes_recv = 3500000
                bytes_sent = 3500000
                bandwidth_rand = lambda x: random.randint(
                    max(x - 250000, 0), max(x + 250000, 0))
            elif period == '30m':
                date_end = date - datetime.timedelta(minutes=date.minute % 30)
                date_cur = date_end - datetime.timedelta(days=7)
                date_step = datetime.timedelta(minutes=30)
                bytes_recv = 21000000
                bytes_sent = 21000000
                bandwidth_rand = lambda x: random.randint(
                    max(x - 2000000, 0), max(x + 2000000, 0))
            elif period == '2h':
                date_end = date - datetime.timedelta(minutes=date.minute,
                    hours=date.hour % 2)
                date_cur = date_end - datetime.timedelta(days=30)
                date_step = datetime.timedelta(hours=2)
                bytes_recv = 84000000
                bytes_sent = 84000000
                bandwidth_rand = lambda x: random.randint(
                    max(x - 2000000, 0), max(x + 2000000, 0))
            elif period == '1d':
                date_end = date - datetime.timedelta(minutes=date.minute,
                    hours=date.hour)
                date_cur = date_end - datetime.timedelta(days=365)
                date_step = datetime.timedelta(days=1)
                bytes_recv = 1008000000
                bytes_sent = 1008000000
                bandwidth_rand = lambda x: random.randint(
                    max(x - 100000000, 0), max(x + 100000000, 0))

            data_p = {
                'received': [],
                'received_total': 0,
                'sent': [],
                'sent_total': 0,
            }
            data[period] = data_p

            while date_cur < date_end:
                date_cur += date_step

                timestamp = int(date_cur.strftime('%s'))
                bytes_recv = bandwidth_rand(bytes_recv)
                bytes_sent = bandwidth_rand(bytes_sent)

                data_p['received'].append((timestamp, bytes_recv))
                data_p['received_total'] += bytes_recv
                data_p['sent'].append((timestamp, bytes_sent))
                data_p['sent_total'] += bytes_sent

        if len(periods) == 1:
            path = os.path.join(app_server.data_path,
                'demo_bandwidth_%s' % periods[0])
            with open(path, 'w') as demo_file:
                demo_file.write(json.dumps(data[periods[0]]))
            return data[periods[0]]
        else:
            path = os.path.join(app_server.data_path, 'demo_bandwidth')
            with open(path, 'w') as demo_file:
                demo_file.write(json.dumps(data))
            return data
