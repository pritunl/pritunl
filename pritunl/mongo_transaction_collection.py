from constants import *
from exceptions import *
from descriptors import *
from mongo_object import MongoObject
from mongo_transaction_action import MongoTransactionAction
import mongo
import pymongo
import collections
import datetime
import bson
import logging

logger = logging.getLogger(APP_NAME)

class MongoTransactionCollection:
    def __init__(self, actions, data=None):
        self._actions = actions
        self._data = data

    def __getattr__(self, name):
        if name in MONGO_ACTION_METHODS:
            return MongoTransactionAction(self._actions, name)
        elif name == 'bulk' and self._data:
            self._data[1] = True
            return lambda: MongoTransactionCollection(self._actions)
        elif name == 'rollback' and self._data:
            return lambda: MongoTransactionCollection(self._data[3])
        elif name == 'post' and self._data:
            return lambda: MongoTransactionCollection(self._data[4])
        elif name == BULK_EXECUTE and self._data:
            self._data[2] = BULK_EXECUTE
            return lambda: MongoTransactionCollection(self._actions)
        else:
            raise AttributeError('MongoTransactionCollection ' +
                'instance has no attribute %r' % name)
