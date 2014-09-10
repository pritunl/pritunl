from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.mongo_object import MongoObject
import pritunl.mongo as mongo
import pymongo
import bson
import datetime
import logging
import collections

_task_types = {}
_tasks = collections.defaultdict(lambda: collections.defaultdict(lambda: []))
logger = logging.getLogger(APP_NAME)

def add_task(task_cls, hours=None, minutes=None):
    if hours is not None or minutes is not None:
        if hours is None:
            hours = ('all',)
        elif isinstance(hours, int):
            hours = (hours,)

        if minutes is None:
            minutes = (0,)
        elif isinstance(minutes, int):
            minutes = (minutes,)

        for hour in hours:
            for minute in minutes:
                _tasks[hour][minute].append(task_cls)

    _task_types[task_cls.type] = task_cls

class Task(MongoObject):
    fields = {
        'attempts',
        'type',
        'ttl',
        'ttl_timestamp',
    }
    fields_default = {
        'attempts': 0,
        'ttl': MONGO_TASK_TTL,
    }
    type = None

    def __init__(self, **kwargs):
        MongoObject.__init__(self, **kwargs)
        self.type = self.type
        self.runner_id = bson.ObjectId()

    @static_property
    def collection(cls):
        return mongo.get_collection('task')

    def claim(self):
        try:
            response = self.collection.update({
                '_id': bson.ObjectId(self.id),
                '$or': [
                    {'runner_id': self.runner_id},
                    {'runner_id': {'$exists': False}},
                ],
            }, {'$set': {
                'runner_id': self.runner_id,
                'type': self.type,
                'ttl': self.ttl,
                'ttl_timestamp': datetime.datetime.utcnow() + \
                    datetime.timedelta(seconds=self.ttl),
            }}, upsert=True)
        except pymongo.errors.DuplicateKeyError:
            return False
        return response.get('updatedExisting') or response.get('upserted')

    def run(self):
        if not self.claim():
            return
        try:
            self.attempts += 1
            if self.attempts <= MONGO_TASK_MAX_ATTEMPTS:
                self.commit('attempts')
                self.task()

            self.complete()
        except:
            logger.exception('Error running task. %r' % {
                'task_id': self.id,
                'task_type': self.type,
            })

    def complete(self):
        self.remove()

    def task(self):
        pass

    @classmethod
    def iter_tasks(cls, spec=None):
        for doc in cls.collection.find(spec or {}):
            yield _task_types[doc['type']](doc=doc)
