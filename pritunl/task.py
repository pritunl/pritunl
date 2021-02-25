from pritunl.helpers import *
from pritunl.constants import *
from pritunl import settings
from pritunl import mongo
from pritunl import logger
from pritunl import utils

import pymongo
import datetime
import collections

_task_types = {}
tasks = collections.defaultdict(
    lambda: collections.defaultdict(lambda: collections.defaultdict(list)))
tasks_on_start = []

class Task(mongo.MongoObject):
    fields = {
        'attempts',
        'type',
        'state',
        'ttl',
        'ttl_timestamp',
        'timestamp',
    }
    fields_default = {
        'state': PENDING,
        'attempts': 0,
        'ttl': settings.mongo.task_ttl,
    }
    type = None

    def __init__(self, run_id=None, **kwargs):
        mongo.MongoObject.__init__(self)
        self.type = self.type
        self.runner_id = utils.ObjectId()

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('tasks')

    def claim_commit(self, fields=None):
        doc = self.get_commit_doc(fields=fields)

        doc['state'] = PENDING
        doc['attempts'] = self.attempts
        doc['runner_id'] = self.runner_id
        doc['ttl_timestamp'] = utils.now() + \
            datetime.timedelta(seconds=self.ttl)
        doc['timestamp'] = utils.now()

        try:
            response = self.collection.update({
                '_id': self.id,
                '$and': [
                    {'$or': [
                        {'state': {'$ne': COMPLETE}},
                        {'state': {'$exists': False}},
                    ]},
                    {'$or': [
                        {'runner_id': self.runner_id},
                        {'runner_id': {'$exists': False}},
                    ]},
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
            logger.exception('Error running task', 'task',
                task_id=self.id,
                task_type=self.type,
            )

    def complete(self):
        self.collection.update({
            '_id': self.id,
            '$or': [
                {'runner_id': self.runner_id},
                {'runner_id': {'$exists': False}},
            ],
        }, {
            '$set': {
                'state': COMPLETE,
            },
        })

    def task(self):
        pass

def iter_tasks(spec=None):
    for doc in Task.collection.find(spec or {}):
        task = _task_types.get(doc['type'])
        if task:
            yield task(doc=doc)

def add_task(task_cls, hours=None, minutes=None, seconds=None,
        run_on_start=False):
    if run_on_start:
        tasks_on_start.append(task_cls)

    if hours is not None or minutes is not None or seconds is not None:
        if hours is None:
            hours = ('all',)
        elif isinstance(hours, int):
            hours = (hours,)

        if hours != ('all',) and minutes is None:
            minutes = (0,)
        elif minutes is None:
            minutes = ('all',)
        elif isinstance(minutes, int):
            minutes = (minutes,)

        if seconds is None:
            seconds = (0,)
        elif isinstance(seconds, int):
            seconds = (seconds,)

        for hour in hours:
            for minute in minutes:
                for second in seconds:
                    tasks[hour][minute][second].append(task_cls)

    _task_types[task_cls.type] = task_cls
