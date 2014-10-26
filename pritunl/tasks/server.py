from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import mongo
from pritunl import logger
from pritunl import transaction
from pritunl import event
from pritunl import server
from pritunl import listener
from pritunl import messenger
from pritunl import utils
from pritunl import task

import pymongo
import collections
import datetime
import bson
import threading
import time
import random
import hashlib

class TaskServer(task.Task):
    type = 'server'

    @cached_static_property
    def server_collection(cls):
        return mongo.get_collection('servers')

    @interrupter
    def task(self):
        try:
            timestamp_spec = utils.now() - datetime.timedelta(
                seconds=settings.vpn.server_ping_ttl)

            docs = self.server_collection.find({
                'instances.ping_timestamp': {'$lt': timestamp_spec},
            }, {
                '_id': True,
                'instances': True,
            })

            yield

            for doc in docs:
                for instance in doc['instances']:
                    if instance['ping_timestamp'] < timestamp_spec:
                        self.server_collection.update({
                            '_id': doc['_id'],
                            'instances.instance_id': instance['instance_id'],
                        }, {
                            '$pull': {
                                'instances': {
                                    'instance_id': instance['instance_id'],
                                },
                            },
                            '$inc': {
                                'instances_count': -1,
                            },
                        })

            yield

            response = self.server_collection.aggregate([
                {'$match': {
                    'status': ONLINE,
                    'start_timestamp': {'$lt': timestamp_spec},
                }},
                {'$project': {
                    '_id': True,
                    'hosts': True,
                    'instances': True,
                    'replica_count': True,
                    'offline_instances_count': {
                        '$subtract': [
                            '$replica_count',
                            '$instances_count',
                        ],
                    }
                }},
                {'$match': {
                    'offline_instances_count': {'$gt': 0},
                }},
            ])['result']

            yield

            for doc in response:
                active_hosts = set([x['host_id'] for x in doc['instances']])
                hosts = list(set(doc['hosts']) - active_hosts)
                if not hosts:
                    continue

                prefered_host = random.sample(hosts,
                    min(doc['replica_count'], len(hosts)))
                messenger.publish('servers', 'start', extra={
                    'server_id': doc['_id'],
                    'send_events': True,
                    'prefered_hosts': prefered_host,
                })
        except GeneratorExit:
            raise
        except:
            logger.exception('Error checking server states.')

        yield interrupter_sleep(settings.vpn.server_ping)

task.add_task(TaskServer, seconds=xrange(0, 60, settings.vpn.server_ping))
