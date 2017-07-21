from pritunl.queue.queue import Queue

from pritunl.constants import *
from pritunl import messenger

queue_types = {}
reserve_types = {}

def get(doc):
    return queue_types[doc['type']](doc=doc)

def start(queue_type, transaction=None, block=False, block_timeout=60,
        *args, **kwargs):
    que = queue_types[queue_type](*args, **kwargs)
    que.start(transaction=transaction, block=block,
        block_timeout=block_timeout)
    return que

def stop(queue_id=None, spec=None, transaction=None):
    if queue_id is not None:
        pass
    elif spec is not None:
        doc = Queue.collection.find_one(spec, {
            '_id': True,
        })
        if not doc:
            return
        queue_id = doc['_id']
    else:
        raise ValueError('Must provide queue_id or spec')

    messenger.publish('queue', [STOP, queue_id], transaction=transaction)

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

def find(spec):
    return Queue.collection.find_one(spec)
