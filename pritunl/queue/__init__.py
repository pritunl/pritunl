from pritunl.queue.com import QueueCom

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import settings
from pritunl.queue import com
from pritunl import logger
from pritunl import mongo
from pritunl import messenger

import bson
import datetime
import logging
import threading
import time
import importlib
import os

queue_types = {}
reserve_types = {}

class Queue(mongo.MongoObject):
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
        'priority': LOW,
        'retry': True,
        'attempts': 0,
        'ttl': settings.mongo.queue_ttl,
    }
    type = None
    cpu_type = NORMAL_CPU
    reserve_id = None

    def __init__(self, priority=None, retry=None, **kwargs):
        mongo.MongoObject.__init__(self, **kwargs)
        self.type = self.type
        self.reserve_id = self.reserve_id
        self.runner_id = bson.ObjectId()
        self.claimed = False
        self.queue_com = QueueCom()
        self.keep_alive_thread = None

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

    def _keep_alive_thread(self):
        while True:
            time.sleep(self.ttl - 5)
            if self.queue_com.state in (COMPLETE, STOPPED):
                break
            response = self.collection.update({
                '_id': bson.ObjectId(self.id),
                'runner_id': self.runner_id,
            }, {'$set': {
                'ttl_timestamp': utils.now() + \
                    datetime.timedelta(seconds=self.ttl),
            }})
            if response['updatedExisting']:
                logger.debug('Queue keep alive updated', 'queue',
                    queue_id=self.id,
                    queue_type=self.type,
                )

                messenger.publish('queue', [UPDATE, self.id])
            else:
                logger.debug('Queue keep alive lost reserve', 'queue',
                    queue_id=self.id,
                    queue_type=self.type,
                )

                self.queue_com.state_lock.acquire()
                try:
                    self.queue_com.state = STOPPED
                finally:
                    self.queue_com.state_lock.release()
                raise QueueStopped('Lost reserve, queue stopped', {
                    'queue_id': self.id,
                    'queue_type': self.type,
                    })

        logger.debug('Queue keep alive thread ended', 'queue',
            queue_id=self.id,
            queue_type=self.type,
        )

    def keep_alive(self):
        if self.keep_alive_thread:
            return
        self.keep_alive_thread = threading.Thread(
            target=self._keep_alive_thread)
        self.keep_alive_thread.daemon = True
        self.keep_alive_thread.start()

    def start(self, transaction=None, block=False, block_timeout=30):
        self.ttl_timestamp = utils.now() + \
            datetime.timedelta(seconds=self.ttl)
        self.commit(transaction=transaction)

        if block:
            if transaction:
                raise TypeError('Cannot use transaction when blocking')
            cursor_id = messenger.get_cursor_id('queue')

        extra = {
            'queue_doc': self.export()
        }

        messenger.publish('queue', [PENDING, self.id], extra=extra,
            transaction=transaction)

        if block:
            last_update = time.time()
            while True:
                for msg in messenger.subscribe('queue', cursor_id=cursor_id,
                        timeout=block_timeout):
                    cursor_id = msg['_id']
                    try:
                        if msg['message'] == [COMPLETE, self.id]:
                            return
                        elif msg['message'] == [UPDATE, self.id]:
                            last_update = time.time()
                            break
                        elif msg['message'] == [ERROR, self.id]:
                            raise QueueTaskError('Error occured running ' +
                                'queue task', {
                                    'queue_id': self.id,
                                    'queue_type': self.type,
                                })
                    except TypeError:
                        pass

                if (time.time() - last_update) >= block_timeout:
                    raise QueueTimeout('Blocking queue timed out.', {
                        'queue_id': self.id,
                        'queue_type': self.type,
                    })

    def claim_commit(self, fields=None):
        doc = self.get_commit_doc(fields=fields)

        doc['runner_id'] = self.runner_id
        doc['ttl_timestamp'] = utils.now() + \
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

        if self.claimed:
            self.keep_alive()

            logger.debug('Queue claimed', 'queue',
                queue_id=self.id,
                queue_type=self.type,
            )

        return response['updatedExisting']

    @classmethod
    def reserve(cls, reserve_id, reserve_data, block=False, block_timeout=30):
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
        self.queue_com.state = RUNNING

        try:
            if self.state == PENDING:
                self.attempts += 1

                if self.attempts > 1 and not self.retry:
                    logger.debug('Non retry queue exceeded attemps', 'queue',
                        queue_id=self.id,
                        queue_type=self.type,
                    )

                    self.remove()
                    return
                elif self.attempts > settings.mongo.queue_max_attempts:
                    self.state = ROLLBACK
                    if not self.claim_commit('state'):
                        return
                else:
                    if not self.claim_commit('attempts'):
                        return

                    logger.debug('Starting queue task', 'queue',
                        queue_id=self.id,
                        queue_type=self.type,
                    )
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
                    logger.debug('Starting queue post_task', 'queue',
                        queue_id=self.id,
                        queue_type=self.type,
                    )

                    self.post_task()
                elif self.state == ROLLBACK:
                    logger.debug('Starting queue rollback_task', 'queue',
                        queue_id=self.id,
                        queue_type=self.type,
                    )

                    self.rollback_task()

                if self.has_post_work:
                    logger.debug('Starting queue complete_task', 'queue',
                        queue_id=self.id,
                        queue_type=self.type,
                    )

                    self.complete_task()

            if self.claimed:
                self.complete()
        except:
            if self.queue_com.state is not STOPPED:
                logger.exception('Error running task in queue. %r' % {
                    'queue_id': self.id,
                    'queue_type': self.type,
                })
                messenger.publish('queue', [ERROR, self.id])
        finally:
            self.queue_com.state_lock.acquire()
            try:
                self.queue_com.state = COMPLETE
            finally:
                self.queue_com.state_lock.release()

    def pause(self):
        self.queue_com.state_lock.acquire()
        try:
            if self.queue_com.state == RUNNING and self.pause_task():
                self.queue_com.state = PAUSED
                return True
            return False
        finally:
            self.queue_com.state_lock.release()

    def resume(self):
        self.queue_com.state_lock.acquire()
        try:
            if self.queue_com.state == PAUSED and self.resume_task():
                self.queue_com.state = RUNNING
                return True
            return False
        finally:
            self.queue_com.state_lock.release()

    def stop(self):
        self.queue_com.state_lock.acquire()
        try:
            if self.queue_com.state == RUNNING and self.stop_task():
                self.queue_com.state = STOPPED
                return True
            return False
        finally:
            self.queue_com.state_lock.release()

    def complete(self):
        messenger.publish('queue', [COMPLETE, self.id])
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
        return False

    def pause_task(self):
        return False

    def resume_task(self):
        pass

    def complete_task(self):
        """not_overridden"""
        pass

def get(doc):
    return queue_types[doc['type']](doc=doc)

def start(queue_type, transaction=None, block=False, block_timeout=30,
        *args, **kwargs):
    que = queue_types[queue_type](*args, **kwargs)
    que.start(transaction=transaction, block=block,
        block_timeout=block_timeout)
    return que

def iter_queues(spec=None):
    for doc in Queue.collection.find(spec or {}).sort('priority'):
        yield queue_types[doc['type']](doc=doc)

def add_queue(cls):
    queue_types[cls.type] = cls
    return cls

def add_reserve(reserve_type):
    def add_reserve_wrap(func):
        reserve_types[reserve_type] = func
        return func
    return add_reserve_wrap

def reserve(reserve_type, *args, **kwargs):
    return reserve_types[reserve_type](*args, **kwargs)
