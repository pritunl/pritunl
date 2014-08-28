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
import threading
import zlib
import json

logger = logging.getLogger(APP_NAME)

def object_hook_handler(obj):
    object_data = obj.get('__OBJ__')
    if object_data:
        object_type, object_data = object_data
        if object_type == 'OID':
            return bson.ObjectId(object_id)
        elif object_type == 'DATE':
            return datetime.datetime.fromtimestamp(object_data)
    return obj

def json_default(obj):
    if isinstance(obj, bson.ObjectId):
        return {'__OBJ__': ['OID', str(obj)]}
    elif isinstance(obj, datetime.datetime):
        return {'__OBJ__': ['DATE', time.mktime(obj.timetuple()) + (obj.microsecond / 1000000.)]}
    return obj

class MongoTransaction:
    def __init__(self, id=None, lock_id=None, priority=NORMAL,
            ttl=MONGO_TRAN_TTL):
        self.action_sets = []
        self.priority = priority
        self.ttl = ttl

        if id is None:
            self.id = bson.ObjectId()
        else:
            self.id = id

        if lock_id is None:
            self.lock_id = bson.ObjectId()
        else:
            self.lock_id = lock_id

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
            func, args, kwargs = action

            tran_str += '    .%s(' % func

            if args:
                tran_str += ', '.join(['%s' % x for x in args])

            if kwargs:
                tran_str += ', '
                tran_str += ', '.join(['%s=%s' % (x, y)
                    for x, y in kwargs.items()])

            tran_str += ')\n'
        return tran_str

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
                'ttl_timestamp': datetime.datetime.utcnow() + \
                    datetime.timedelta(seconds=self.ttl),
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

    def _run_collection_actions(self, obj, actions):
        for action in actions:
            func, args, kwargs = action
            obj = getattr(obj, func)(*args or [], **kwargs or {})

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
                'ttl_timestamp': datetime.datetime.utcnow() + \
                    datetime.timedelta(seconds=self.ttl),
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
        actions_json = json.dumps(self.action_sets, default=json_default)
        actions_json_zlib = zlib.compress(actions_json)

        self.collection.insert({
            '_id': self.id,
            'state': PENDING,
            'priority': self.priority,
            'lock_id': self.lock_id,
            'ttl': self.ttl,
            'ttl_timestamp': datetime.datetime.utcnow() + \
                datetime.timedelta(seconds=self.ttl),
            'attempts': 1,
            'actions': bson.Binary(actions_json_zlib),
        }, upsert=True)

        try:
            self._run_actions()
            self.collection.remove(self.id)
        except:
            logger.exception('Error occured running ' +
                'transaction actions initial. %r' % {
                    'transaction_id': str(self.id),
                })
