from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.messenger import Messenger
from pritunl.mongo_object import MongoObject
import pritunl.mongo as mongo
import bson
import datetime
import logging

queue_types = {}
logger = logging.getLogger(APP_NAME)

def add_queue(queue_type, QueueClass):
    queue_types[queue_type] = QueueClass

class Queue(MongoObject):
    fields = {
        'state',
        'priority',
        'attempts',
        'type',
        'reserve_id',
        'ttl',
        'ttl_timestamp',
    }
    fields_default = {
        'state': PENDING,
        'priority': NORMAL,
        'attempts': 0,
        'ttl': MONGO_QUEUE_TTL,
    }
    type = None
    reserve_id = None

    def __init__(self, **kwargs):
        MongoObject.__init__(self, **kwargs)
        self.type = self.type
        self.reserve_id = self.reserve_id
        self.runner_id = bson.ObjectId()
        self.claimed = False

    @static_property
    def collection(cls):
        return mongo.get_collection('queue')

    @cached_property
    def has_post_work(self):
        return any((
            self.post_task.__doc__ != 'not_overridden',
            self.complete_task.__doc__ != 'not_overridden',
        ))

    def start(self, transaction=None, block=False, block_timeout=30):
        self.ttl_timestamp = datetime.datetime.utcnow() + \
            datetime.timedelta(seconds=self.ttl)
        self.commit(transaction=transaction)
        messenger = Messenger('queue')

        if block:
            if transaction:
                raise TypeError('Cannot use transaction when blocking')
            cursor_id = messenger.get_cursor_id()

        messenger.publish([PENDING, self.id], transaction=transaction)

        if block:
            for msg in messenger.subscribe(cursor_id=cursor_id,
                    timeout=block_timeout):
                try:
                    if msg['message'] == [COMPLETE, self.id]:
                        return
                except TypeError:
                    pass
            raise QueueTimeout('Blocking queue timed out.', {
                'queue_id': self.id,
                'queue_type': self.type,
            })

    def claim_commit(self, fields=None):
        doc = self.get_commit_doc(fields=fields)

        doc['runner_id'] = self.runner_id
        doc['ttl_timestamp'] = datetime.datetime.utcnow() + \
            datetime.timedelta(seconds=self.ttl)

        response = self.collection.update({
            '_id': bson.ObjectId(self.id),
            '$or': [
                {'runner_id': self.runner_id},
                {'runner_id': {'$exists': False}},
            ],
        }, {
            '$set': doc
        })

        self.claimed = response['updatedExisting']

        return response['updatedExisting']

    def run(self):
        try:
            if self.state == PENDING:
                self.attempts += 1
                if self.attempts > MONGO_QUEUE_MAX_ATTEMPTS:
                    self.state = ROLLBACK
                    if not self.claim_commit('state'):
                        return
                else:
                    if not self.claim_commit('attempts'):
                        return

                    self.task()

                    self.state = COMMITTED
                    self.commit('state')

                if not self.claim():
                    return

            if self.state == COMMITTED:
                self.post_task()
            elif self.state == ROLLBACK:
                self.rollback_task()

            self.complete_task()

            if self.claimed:
                self.complete()
        except:
            logger.exception('Error running task in queue. %r' % {
                'queue_id': self.id,
                'queue_type': self.type,
            })

    def complete(self):
        messenger = Messenger('queue')
        messenger.publish([COMPLETE, self.id])
        self.remove()

    def task(self):
        pass

    def post_task(self):
        """not_overridden"""
        pass

    def rollback_task(self):
        pass

    def complete_task(self):
        """not_overridden"""
        pass

    @classmethod
    def iter_queues(cls, spec=None):
        for doc in cls.collection.find(spec or {}).sort('priority'):
            yield queue_types[doc['type']](doc=doc)
