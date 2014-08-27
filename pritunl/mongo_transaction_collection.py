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
    def __init__(self, parent_actions, parent_data=None):
        self._parent_actions = parent_actions
        self._parent_data = parent_data

    def __getattr__(self, name):
        if name in MONGO_ACTION_METHODS:
            return MongoTransactionAction(self._parent_actions, name)
        elif name == 'bulk' and self._parent_data:
            self._parent_data[1] = True
            return lambda: MongoTransactionCollection(self._parent_actions)
        elif name == 'rollback' and self._parent_data:
            return lambda: MongoTransactionCollection(self._parent_data[3])
        elif name == BULK_EXECUTE and self._parent_data:
            self._parent_data[2] = BULK_EXECUTE
            return lambda: MongoTransactionCollection(self._parent_actions)
        else:
            raise AttributeError('MongoTransactionCollection ' +
                'instance has no attribute %r' % name)
