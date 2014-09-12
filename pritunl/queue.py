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

def add_queue(queue_cls):
    queue_types[queue_cls.type] = queue_cls

class Queue(MongoObject):
    fields = {
        'state',
        'priority',
        'retry',
        'attempts',
        'type',
        'reserve_id',
        'reserve_data',
        'ttl',
        'ttl_timestamp',
    }
    fields_default = {
        'state': PENDING,
        'priority': NORMAL,
        'retry': True,
        'attempts': 0,
        'ttl': MONGO_QUEUE_TTL,
    }
    type = None
    reserve_id = None

    def __init__(self, priority=None, retry=None, **kwargs):
        MongoObject.__init__(self, **kwargs)
        self.type = self.type
        self.reserve_id = self.reserve_id
        self.runner_id = bson.ObjectId()
        self.claimed = False
        self.stopped = False

        if priority is not None:
            self.priority = priority
        if retry is not None:
            self.retry = retry

    @cached_static_property
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
        messenger = Messenger()

        if block:
            if transaction:
                raise TypeError('Cannot use transaction when blocking')
            cursor_id = messenger.get_cursor_id('queue')

        messenger.publish('queue', [PENDING, self.id], transaction=transaction)

        if block:
            for msg in messenger.subscribe('queue', cursor_id=cursor_id,
                    timeout=block_timeout):
                try:
                    if msg['message'] == [COMPLETE, self.id]:
                        return
                    elif msg['message'] == [ERROR, self.id]:
                        raise QueueTaskError('Error occured running ' +
                            'queue task', {
                                'queue_id': self.id,
                                'queue_type': self.type,
                            })
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
            '$set': doc,
        })

        self.claimed = response['updatedExisting']

        return response['updatedExisting']

    @classmethod
    def reserve(cls, reserve_id, reserve_data, block=False, block_timeout=30):
        messenger = Messenger()

        if block:
            cursor_id = messenger.get_cursor_id('queue')

        doc = cls.collection.find_and_modify({
            'state': PENDING,
            'reserve_id': reserve_id,
            'reserve_data': None,
        }, {'$set': {
            'reserve_data': reserve_data,
        }})
        if not doc:
            return

        if block:
            for msg in messenger.subscribe('queue', cursor_id=cursor_id,
                    timeout=block_timeout):
                try:
                    if msg['message'] == [COMPLETE, str(doc['_id'])]:
                        return doc
                    elif msg['message'] == [ERROR, str(doc['_id'])]:
                        raise QueueTaskError('Error occured running ' +
                            'queue task', {
                                'queue_id': str(doc['_id']),
                                'queue_type': doc['type'],
                            })
                except TypeError:
                    pass
            raise QueueTimeout('Blocking queue reserve timed out', {
                'queue_id': str(doc['_id']),
                'queue_type': doc['type'],
            })
        else:
            return doc

    def run(self):
        try:
            if self.state == PENDING:
                self.attempts += 1

                if self.attempts > 1 and not self.retry:
                    self.remove()
                    return
                elif self.attempts > MONGO_QUEUE_MAX_ATTEMPTS:
                    self.state = ROLLBACK
                    if not self.claim_commit('state'):
                        return
                else:
                    if not self.claim_commit('attempts'):
                        return

                    self.task()

                    if self.attempts > 1:
                        self.repeat_task()

                    if self.has_post_work:
                        self.state = COMMITTED
                        if not self.claim_commit('state'):
                            return

            if self.has_post_work or self.state == ROLLBACK:
                if not self.claimed and not self.claim_commit():
                    return

                if self.state == COMMITTED:
                    self.post_task()
                elif self.state == ROLLBACK:
                    self.rollback_task()

                if self.has_post_work:
                    self.complete_task()

            if self.claimed:
                self.complete()
        except:
            if not self.stopped:
                logger.exception('Error running task in queue. %r' % {
                    'queue_id': self.id,
                    'queue_type': self.type,
                })
                Messenger().publish('queue', [ERROR, self.id])

    def stop(self):
        self.stopped = self.stop_task()

    def complete(self):
        Messenger().publish('queue', [COMPLETE, self.id])
        self.remove()

    def task(self):
        pass

    def repeat_task(self):
        pass

    def post_task(self):
        """not_overridden"""
        pass

    def rollback_task(self):
        pass

    def stop_task(self):
        return True

    def complete_task(self):
        """not_overridden"""
        pass

    @classmethod
    def iter_queues(cls, spec=None):
        for doc in cls.collection.find(spec or {}).sort('priority'):
            yield queue_types[doc['type']](doc=doc)
