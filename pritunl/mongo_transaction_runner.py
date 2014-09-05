from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.mongo_object import MongoObject
from pritunl.mongo_transaction import MongoTransaction
import pritunl.mongo as mongo
import pymongo
import collections
import datetime
import bson
import logging
import threading
import time

logger = logging.getLogger(APP_NAME)

class MongoTransactionRunner:
    @static_property
    def collection(cls):
        return mongo.get_collection('transaction')

    def check_thread(self):
        while True:
            spec = {
                'ttl_timestamp': {'$lt': datetime.datetime.utcnow()},
            }

            for doc in self.collection.find(spec).sort('priority'):
                try:
                    tran = MongoTransaction(doc=doc)
                    tran.run()
                except:
                    logger.exception('Failed to run transaction. %r' % {
                        'transaction_id': str(doc['_id']),
                    })

            time.sleep(3)

    def start(self):
        thread = threading.Thread(target=self.check_thread)
        thread.daemon = True
        thread.start()
