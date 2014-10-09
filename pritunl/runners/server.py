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

import pymongo
import collections
import datetime
import bson
import threading
import time

def _on_msg(msg):
    if msg['message'] != 'start':
        return

    try:
        svr = server.get_server(msg['server_id'])
        if settings.local.host_id not in svr.hosts:
            return
        svr.run()
    except:
        logger.exception('Failed to run server.')

def _server_check_thread():
    collection = mongo.get_collection('servers')

    while True:
        try:
            response = collection.update({
                'ping_timestamp': {
                    '$lt': datetime.datetime.utcnow() - datetime.timedelta(
                        seconds=settings.vpn.server_ping_ttl),
                },
            }, {
                '$set': {
                    'status': False,
                    'start_timestamp': False,
                    'ping_timestamp': False,
                },
                '$unset': {
                    'instance_id': '',
                },
            })

            if response['updatedExisting']:
                event.Event(type=SERVERS_UPDATED)
        except:
            logger.exception('Error checking server states.')

        time.sleep(settings.vpn.server_ping)

def start_server():
    thread = threading.Thread(target=_server_check_thread)
    thread.daemon = True
    thread.start()

    listener.add_listener('servers', _on_msg)
