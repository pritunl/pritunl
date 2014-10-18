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

import pymongo
import collections
import datetime
import bson
import threading
import time
import random
import hashlib

def _on_msg(msg):
    if msg['message'] != 'start':
        return

    try:
        svr = server.get_server(msg['server_id'])
        if settings.local.host_id not in svr.hosts:
            return

        for instance in svr.instances:
            if instance['host_id'] == settings.local.host_id:
                return

        prefered_host = msg.get('prefered_host')

        if prefered_host and settings.local.host_id != prefered_host:
            time.sleep(0.1)

        svr.run(send_events=msg.get('send_events'))
    except:
        logger.exception('Failed to run server.')

def _server_check_thread():
    collection = mongo.get_collection('servers')

    while True:
        try:
            timestamp_spec = utils.now() - datetime.timedelta(
                seconds=settings.vpn.server_ping_ttl)

            docs = collection.find({
                'instances.ping_timestamp': {'$lt': timestamp_spec},
            }, {
                '_id': True,
                'instances': True,
            })

            for doc in docs:
                for instance in doc['instances']:
                    if instance['ping_timestamp'] < timestamp_spec:
                        collection.update({
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

            response = collection.aggregate([
                {'$match': {
                    'status': True,
                    'start_timestamp': {'$lt': timestamp_spec},
                }},
                {'$project': {
                    '_id': True,
                    'hosts': True,
                    'instances': True,
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

            for doc in response:
                active_hosts = set([x['host_id'] for x in doc['instances']])
                hosts = list(set(doc['hosts']) - active_hosts)
                if not hosts:
                    continue
                prefered_host = random.choice(hosts)

                messenger.publish('servers', 'start', extra={
                    'server_id': str(doc['_id']),
                    'send_events': True,
                    'prefered_host': prefered_host,
                })
        except:
            logger.exception('Error checking server states.')

        time.sleep(settings.vpn.server_ping)

def start_server():
    thread = threading.Thread(target=_server_check_thread)
    thread.daemon = True
    thread.start()

    listener.add_listener('servers', _on_msg)
