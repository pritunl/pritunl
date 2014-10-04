from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl import mongo
from pritunl import logger
from pritunl import transaction

import pymongo
import collections
import datetime
import bson
import threading
import time

def _check_thread():
    collection = mongo.get_collection('transaction')

    while True:
        spec = {
            'ttl_timestamp': {'$lt': datetime.datetime.utcnow()},
        }

        for doc in collection.find(spec).sort('priority'):
            try:
                tran = transaction.Transaction(doc=doc)
                tran.run()
            except:
                logger.exception('Failed to run transaction. %r' % {
                    'transaction_id': str(doc['id']),
                })

        time.sleep(settings.mongo.tran_ttl)

def start_transaction():
    thread = threading.Thread(target=_check_thread)
    thread.daemon = True
    thread.start()
