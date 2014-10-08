from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import settings
from pritunl import mongo
from pritunl import logger
from pritunl import transaction
from pritunl import event

import pymongo
import collections
import datetime
import bson
import threading
import time

def _server_check_thread():
    collection = mongo.get_collection('servers')

    while True:
        try:
            response = collection.update({
                'ping_timestamp': {
                    '$lt': datetime.datetime.utcnow() - datetime.timedelta(
                        seconds=settings.vpn.server_ping_ttl),
                },
            }, {'$set': {
                'status': False,
                'instance_id': None,
                'start_timestamp': False,
                'ping_timestamp': False,
            }})

            if response['updatedExisting']:
                event.Event(type=SERVERS_UPDATED)
        except:
            logger.exception('Error checking server states.')

        time.sleep(settings.vpn.server_ping)

def start_server():
    thread = threading.Thread(target=_server_check_thread)
    thread.daemon = True
    thread.start()
