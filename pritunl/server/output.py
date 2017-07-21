from pritunl.constants import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import mongo
from pritunl import event
from pritunl import utils

import pymongo
import datetime

class ServerOutput(object):
    def __init__(self, server_id):
        self.server_id = server_id

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('servers_output')

    def send_event(self, delay=True):
        if delay:
            delay = SERVER_OUTPUT_DELAY
        else:
            delay = None

        event.Event(
            type=SERVER_OUTPUT_UPDATED,
            resource_id=self.server_id,
            delay=delay,
        )

    def clear_output(self):
        self.collection.remove({
            'server_id': self.server_id,
        })
        self.send_event(delay=False)

    def prune_output(self):
        cursor = self.collection.find({
            'server_id': self.server_id,
        }, {
            '_id': True,
            'timestamp': True,
        }).sort('timestamp', pymongo.DESCENDING).skip(settings.vpn.log_lines)

        doc_ids = []
        for doc in cursor:
            doc_ids.append(doc['_id'])

        if doc_ids:
            self.collection.remove({
                '_id': {'$in': doc_ids},
            })

    def push_output(self, output, label=None):
        if '--keepalive' in output:
            return

        label = label or settings.local.host.name

        self.collection.insert({
            'server_id': self.server_id,
            'timestamp': utils.now(),
            'output': '[%s] %s' % (label, output.rstrip('\n')),
        })

        self.prune_output()
        self.send_event()

    def push_message(self, message, *args, **kwargs):
        timestamp = datetime.datetime.now().strftime(
            '%a %b  %d %H:%M:%S %Y').replace('  0', '   ', 1).replace(
            '  ', ' ', 1)
        self.push_output('%s %s' % (timestamp, message), *args, **kwargs)

    def get_output(self):
        if settings.app.demo_mode:
            return DEMO_OUTPUT

        response = self.collection.aggregate([
            {'$match': {
                'server_id': self.server_id,
            }},
            {'$project': {
                '_id': False,
                'timestamp': True,
                'output': True,
            }},
            {'$sort': {
                'timestamp': pymongo.ASCENDING,
            }},
            {'$group': {
                '_id': None,
                'output': {'$push': '$output'},
            }},
        ])

        val = None
        for val in response:
            break

        if val:
            output = val['output']
        else:
            output = []

        return output
