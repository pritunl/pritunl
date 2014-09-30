from pritunl.mongo.transaction import MongoTransaction
from pritunl.mongo.object import MongoObject

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl import mongo
from pritunl import logger

import pymongo
import collections
import datetime
import bson
import threading
import time

class MongoTransactionRunner:
    @cached_static_property
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
                        'transaction_id': str(doc['id']),
                    })

            time.sleep(settings.mongo.tran_ttl)

    def start(self):
        thread = threading.Thread(target=self.check_thread)
        thread.daemon = True
        thread.start()
