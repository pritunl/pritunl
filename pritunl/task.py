from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl import mongo
from pritunl import logger

import pymongo
import bson
import datetime
import collections

_task_types = {}
tasks = collections.defaultdict(lambda: collections.defaultdict(list))

class Task(mongo.MongoObject):
    fields = {
        'attempts',
        'type',
        'ttl',
        'ttl_timestamp',
    }
    fields_default = {
        'attempts': 0,
        'ttl': settings.mongo.task_ttl,
    }
    type = None

    def __init__(self, **kwargs):
        mongo.MongoObject.__init__(self, **kwargs)
        self.type = self.type
        self.runner_id = bson.ObjectId()

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('task')

    def claim_commit(self, fields=None):
        doc = self.get_commit_doc(fields=fields)

        doc['runner_id'] = self.runner_id
        doc['ttl_timestamp'] = datetime.datetime.utcnow() + \
            datetime.timedelta(seconds=self.ttl)

        try:
            response = self.collection.update({
                '_id': bson.ObjectId(self.id),
                '$or': [
                    {'runner_id': self.runner_id},
                    {'runner_id': {'$exists': False}},
                ],
            }, {
                '$set': doc,
            }, upsert=True)
            claimed = bool(response.get('updatedExisting') or response.get(
                'upserted'))
        except pymongo.errors.DuplicateKeyError:
            claimed = False

        self.claimed = claimed
        return claimed

    def run(self):
        try:
            self.attempts += 1
            if self.attempts <= settings.mongo.task_max_attempts:
                if not self.claim_commit():
                    return
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

def iter_tasks(spec=None):
    for doc in Task.collection.find(spec or {}):
        yield _task_types[doc['type']](doc=doc)

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
                tasks[hour][minute].append(task_cls)

    _task_types[task_cls.type] = task_cls

__all__ = (
    'Task',
    'iter_tasks',
    'add_task',
)
