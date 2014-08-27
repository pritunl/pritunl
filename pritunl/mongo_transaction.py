from constants import *
from exceptions import *
from descriptors import *
from mongo_object import MongoObject
from mongo_transaction_collection import MongoTransactionCollection
import mongo
import pymongo
import collections
import datetime
import bson
import logging

logger = logging.getLogger(APP_NAME)

class MongoTransaction:
    def __init__(self, id=None, lock_id=None, priority=NORMAL):
        self.action_sets = []
        self.priority = priority
        self.lock_id

        if id is None:
            self.id = bson.ObjectId()
        else:
            self.id = id

    def __getattr__(self, name):
        if name.endswith('_collection'):
            data = [
                name[:-11], # collection_name
                False, # bulk
                [], # actions
                [], # rollback_actions
            ]
            self.action_sets.append(data)
            return MongoTransactionCollection(data[2], data)
        raise AttributeError(
            'MongoTransaction instance has no attribute %r' % name)

    @static_property
    def collection(cls):
        return mongo.get_collection('transaction')

    def __str__(self):
        tran_str = ''

        for action_set in self.action_sets:
            collection_name, bulk, actions, rollback_actions = action_set

            if actions == BULK_EXECUTE:
                tran_str += '%s_collection.bulk_execute()\n' % collection_name
            elif actions:
                tran_str += '%s_collection%s\n' % (collection_name,
                    '.bulk()' if bulk else '')
                tran_str = self._str_actions(tran_str, actions)

            if rollback_actions:
                tran_str += '%s_collection.rollback()\n' % collection_name
                tran_str = self._str_actions(tran_str, rollback_actions)

        return tran_str.strip()

    def _str_actions(self, tran_str, actions):
        for action in actions:
            func, args, kwargs, child_actions = action

            tran_str += '    .%s(%s' % (
                func,
                ', '.join(['%s' % x for x in args])
            )
            if kwargs:
                tran_str += ', '
                tran_str += ', '.join(['%s=%s' % (x, y)
                    for x, y in kwargs.items()])
            tran_str += ')\n'
            if child_actions:
                tran_str = self._str_actions(tran_str, child_actions)
        return tran_str

    def _run_collection_actions(self, obj, actions):
        for action in actions:
            func, args, kwargs, child_actions = action
            obj = getattr(obj, func)(*args, **kwargs)
            self._run_collection_actions(obj, child_actions)

    def _rollback_actions(self):
        for action_set in self.action_sets:
            collection_name, _, _, rollback_actions = action_set
            collection = mongo.get_collection(collection_name)

            self._run_collection_actions(collection, rollback_actions)

    def rollback_actions(self):
        response = self.collection.update({
            '_id': self.id,
            'state': ROLLBACK,
        }, {
            '$set': {
                'timestamp': datetime.datetime.utcnow(),
            },
            '$inc': {
                'attempts': 1,
            },
        })

        if not response['updatedExisting']:
            return

        try:
            self._rollback_actions()
        except:
            logger.exception('Error occured rolling back ' +
                'transaction actions. %r' % {
                    'transaction_id': str(self.id),
                })
            raise

        self.collection.remove(self.id)

    def _run_actions(self):
        collection_bulks = collections.defaultdict(
            lambda: collection.initialize_ordered_bulk_op())

        for action_set in self.action_sets:
            collection_name, bulk, actions, _ = action_set
            collection = mongo.get_collection(collection_name)

            if bulk:
                collection = collection_bulks[collection_name]
            elif actions == BULK_EXECUTE:
                collection = collection_bulks.pop(collection_name)
                collection.execute()
                continue

            self._run_collection_actions(collection, actions)

    def run_actions(self):
        doc = self.collection.find_and_modify({
            '_id': self.id,
            'state': PENDING,
        }, {
            '$set': {
                'timestamp': datetime.datetime.utcnow(),
            },
            '$inc': {
                'attempts': 1,
            },
        })

        if not doc:
            return
        elif doc['attempts'] > MONGO_TRAN_MAX_ATTEMPTS:
            response = self.collection.update({
                '_id': self.id,
                'state': PENDING,
            }, {
                '$set': {
                    'state': ROLLBACK,
                },
            })
            if response['updatedExisting']:
                self.rollback_actions()
            return

        try:
            self._run_actions()
        except:
            logger.exception('Error occured running ' +
                'transaction actions retry. %r' % {
                    'transaction_id': str(self.id),
                    'attempts': doc['attempts'],
                })
            raise

        self.collection.remove(self.id)

    def commit(self):
        collection_bulks = {}

        for action_set in self.action_sets:
            collection_name, bulk, actions, _ = action_set

            if bulk:
                collection_bulks[collection_name] = True
            elif actions == BULK_EXECUTE:
                collection_bulks.pop(collection_name)

        if len(collection_bulks):
            raise ValueError('Uncommited bulks')

        doc = {
            '_id': self.id,
            'timestamp': datetime.datetime.utcnow(),
            'state': PENDING,
            'priority': self.priority,
            'attempts': 1,
            'actions': bson.Binary(bson.BSON.encode(
                {'data': self.action_sets})),
        }

        if self.lock_id:
            doc['lock_id'] = self.lock_id

        self.collection.insert(doc, upsert=True)

        try:
            self._run_actions()
            self.collection.remove(self.id)
        except:
            logger.exception('Error occured running ' +
                'transaction actions initial. %r' % {
                    'transaction_id': str(self.id),
                })
