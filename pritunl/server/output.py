from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import mongo
from pritunl import event
from pritunl import utils

import pymongo
import os
import json
import random

class ServerOutput(object):
    def __init__(self, server_id):
        self.server_id = server_id

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('servers_output')

    def send_event(self):
        event.Event(type=SERVER_OUTPUT_UPDATED, resource_id=self.server_id,
            delay=OUTPUT_DELAY)

    def clear_output(self):
        self.collection.remove({
            'server_id': self.server_id,
        })
        self.send_event()

    def prune_output(self):
        doc_ids = self.collection.aggregate([
            {'$match': {
                'server_id': self.server_id,
            }},
            {'$project': {
                '_id': True,
                'timestamp': True,
            }},
            {'$sort': {
                'timestamp': pymongo.DESCENDING,
            }},
            {'$skip': settings.vpn.log_lines},
            {'$group': {
                '_id': None,
                'doc_ids': {'$push': '$_id'},
            }},
        ])['result']

        if doc_ids:
            doc_ids = doc_ids[0]['doc_ids']

            self.collection.remove({
                '_id': {'$in': doc_ids},
            })

    def push_output(self, output, label=None):
        label = label or settings.local.host.name

        self.collection.insert({
            'server_id': self.server_id,
            'timestamp': utils.now(),
            'output': '[%s] %s' % (label, output.rstrip('\n')),
        })

        self.prune_output()
        self.send_event()

    def get_output(self):
        output = self.collection.aggregate([
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
        ])['result']

        if output:
            output = output[0]['output']

        return output
