from pritunl.transaction.collection import TransactionCollection

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import settings
from pritunl import mongo
from pritunl import listener
from pritunl import logger
from pritunl import utils

import pymongo
import collections
import datetime
import bson
import threading
import zlib
import json
import time

class Transaction(mongo.MongoObject):
    fields = {
        'state',
        'priority',
        'lock_id',
        'ttl',
        'ttl_timestamp',
        'attempts',
        'actions',
    }
    fields_default = {
        'state': PENDING,
        'priority': NORMAL,
        'attempts': 0,
        'ttl': settings.mongo.tran_ttl,
    }

    def __init__(self, lock_id=None, priority=None,
            ttl=None, **kwargs):
        mongo.MongoObject.__init__(self, **kwargs)

        if lock_id is not None:
            self.lock_id = lock_id
        if self.lock_id is None:
            self.lock_id = bson.ObjectId()

        if priority is not None:
            self.priority = priority

        if ttl is not None:
            self.ttl = ttl

        if self.actions:
            actions_json = zlib.decompress(self.actions)
            self.action_sets = json.loads(actions_json,
                object_hook=utils.json_object_hook_handler)
        else:
            self.action_sets = []

    @cached_static_property
    def transaction_collection(cls):
        return mongo.get_collection('transaction')

    def __str__(self):
        tran_str = ''

        for action_set in self.action_sets:
            collection_name, bulk, actions, rollback_actions, post_actions = \
                action_set

            if actions == BULK_EXECUTE:
                tran_str += '%s_collection.bulk_execute()\n' % collection_name
            elif actions:
                tran_str += '%s_collection%s\n' % (collection_name,
                    '.bulk()' if bulk else '')
                tran_str = self._str_actions(tran_str, actions)

            if rollback_actions:
                tran_str += '%s_collection.rollback()\n' % collection_name
                tran_str = self._str_actions(tran_str, rollback_actions)

            if post_actions:
                tran_str += '%s_collection.post()\n' % collection_name
                tran_str = self._str_actions(tran_str, post_actions)

        return tran_str.strip()

    def collection(self, name):
        return TransactionCollection(collection_name=name,
            action_sets=self.action_sets)

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

    def _run_collection_actions(self, obj, actions):
        for action in actions:
            func, args, kwargs = action
            obj = getattr(obj, func)(*args or [], **kwargs or {})

    def _run_actions(self):
        has_bulk = mongo.has_bulk

        if has_bulk:
            collection_bulks = collections.defaultdict(
                lambda: collection.initialize_ordered_bulk_op())

        for action_set in self.action_sets:
            collection_name, bulk, actions, _, _ = action_set
            collection = mongo.get_collection(collection_name)

            if has_bulk:
                if bulk:
                    collection = collection_bulks[collection_name]
                elif actions == BULK_EXECUTE:
                    collection = collection_bulks.pop(collection_name)
                    collection.execute()
                    continue
            else:
                if bulk:
                    new_action = actions[0]
                    for action in actions[1:]:
                        if action[0] == 'upsert':
                            new_action[2] = {'upsert': True}
                        elif action[0] == 'update':
                            new_action[1].append(action[1][0])
                        elif action[0] == 'remove':
                            new_action[0] = 'remove'
                    actions = [new_action]
                elif actions == BULK_EXECUTE:
                    continue

            self._run_collection_actions(collection, actions)

    def run_actions(self, update_db=True):
        if update_db:
            doc = self.transaction_collection.find_and_modify({
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
            elif doc['attempts'] > settings.mongo.tran_max_attempts:
                response = self.transaction_collection.update({
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
                'transaction actions. %r' % {
                    'transaction_id': str(self.id),
                })
            raise

        response = self.transaction_collection.update({
            '_id': self.id,
            'state': PENDING,
        }, {
            '$set': {
                'state': COMMITTED,
            },
        })
        if not response['updatedExisting']:
            return
        self.run_post_actions()

    def _rollback_actions(self):
        for action_set in self.action_sets:
            collection_name, _, _, rollback_actions, _ = action_set
            collection = mongo.get_collection(collection_name)

            self._run_collection_actions(collection, rollback_actions)

    def rollback_actions(self):
        response = self.transaction_collection.update({
            '_id': self.id,
            'state': ROLLBACK,
        }, {
            '$set': {
                'ttl_timestamp': datetime.datetime.utcnow() + \
                    datetime.timedelta(seconds=self.ttl),
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

        self.transaction_collection.remove(self.id)

    def _run_post_actions(self):
        for action_set in self.action_sets:
            collection_name, _, _, _, post_actions = action_set
            collection = mongo.get_collection(collection_name)

            self._run_collection_actions(collection, post_actions)

    def run_post_actions(self):
        response = self.transaction_collection.update({
            '_id': self.id,
            'state': COMMITTED,
        }, {
            '$set': {
                'ttl_timestamp': datetime.datetime.utcnow() + \
                    datetime.timedelta(seconds=self.ttl),
            },
        })

        if not response['updatedExisting']:
            return

        try:
            self._run_post_actions()
        except:
            logger.exception('Error occured running ' +
                'transaction post actions. %r' % {
                    'transaction_id': str(self.id),
                })
            raise

        self.transaction_collection.remove(self.id)

    def run(self):
        if self.state == PENDING:
            self.run_actions()
        elif self.state == ROLLBACK:
            self.rollback_actions()
        elif self.state == COMMITTED:
            self.run_post_actions()

    def commit(self):
        actions_json = json.dumps(self.action_sets,
            default=utils.json_default)
        actions_json_zlib = zlib.compress(actions_json)

        self.transaction_collection.insert({
            '_id': self.id,
            'state': PENDING,
            'priority': self.priority,
            'lock_id': self.lock_id,
            'ttl': self.ttl,
            'ttl_timestamp': datetime.datetime.utcnow() + \
                datetime.timedelta(seconds=self.ttl),
            'attempts': 1,
            'actions': bson.Binary(actions_json_zlib),
        })

        try:
            self.run_actions(False)
        except:
            pass
