from constants import *
from exceptions import *
from descriptors import *
from messenger import Messenger
from mongo_object import MongoObject
import mongo
import pymongo
import random
import bson
import datetime
import logging

task_types = {}
logger = logging.getLogger(APP_NAME)

class Task(MongoObject):
    fields = {
        'run_time',
        'attempts',
        'type',
        'ttl',
        'ttl_timestamp',
    }
    fields_default = {
        'attempts': 0,
        'ttl': MONGO_TASK_TTL,
    }

    def __init__(self, **kwargs):
        MongoObject.__init__(self, **kwargs)
        self.runner_id = bson.ObjectId()

    @static_property
    def collection(cls):
        return mongo.get_collection('task')

    def claim(self):
        response = self.collection.update({
            '_id': bson.ObjectId(self.id),
            '$or': [
                {'runner_id': self.runner_id},
                {'runner_id': {'$exists': False}},
            ],
        }, {'$set': {
            'runner_id': self.runner_id,
            'ttl_timestamp': datetime.datetime.utcnow() + \
                datetime.timedelta(seconds=self.ttl),
        }})
        return response['updatedExisting']

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
    def iter_tasks(cls, spec={}):
        for doc in cls.collection.find(spec):
            yield task_types[doc['type']](doc=doc)
