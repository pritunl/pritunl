from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import settings
from pritunl import mongo
from pritunl import logger
from pritunl import transaction
from pritunl import event
from pritunl import server
from pritunl import listener
from pritunl import messenger

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

        prefered_host = msg.get('prefered_host')

        # When server start msg is received from check_thread it is
        # possible for multiple servers to send the start message.
        # Attempt to choose a random host based on the current time in
        # seconds so that all servers will choose the same random host
        # if selected in the same one second window
        if not prefered_host:
            rand_hash = hashlib.sha256(str(int(time.time()))).digest()
            rand_gen = random.Random(rand_hash)
            prefered_host = svr.hosts[rand_gen.randint(0, len(svr.hosts) - 1)]

        if settings.local.host_id != prefered_host:
            time.sleep(0.1)

        svr.run(send_events=msg.get('send_events'))
    except:
        logger.exception('Failed to run server.')

def _server_check_thread():
    checked_hosts = set()
    collection = mongo.get_collection('servers')

    while True:
        try:
            spec = {
                'ping_timestamp': {
                    '$lt': datetime.datetime.utcnow() - datetime.timedelta(
                        seconds=settings.vpn.server_ping_ttl),
                },
            }
            doc = {
                '$set': {
                    'clients': {},
                },
                '$unset': {
                    'host_id': '',
                    'instance_id': '',
                },
            }
            project = {
                '_id': True,
                'hosts': True,
                'organizations': True,
            }

            if checked_hosts:
                spec['_id'] = {'$nin': list(checked_hosts)}

            doc = collection.find_and_modify(spec, doc, fields=project)

            if doc:
                checked_hosts.add(doc['_id'])
                messenger.publish('servers', 'start', extra={
                    'server_id': str(doc['_id']),
                    'send_events': True,
                })
                continue
        except:
            logger.exception('Error checking server states.')

        checked_hosts = set()
        time.sleep(settings.vpn.server_ping)

def start_server():
    thread = threading.Thread(target=_server_check_thread)
    thread.daemon = True
    thread.start()

    listener.add_listener('servers', _on_msg)
