from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl.task import Task, _tasks
from pritunl import mongo
import pymongo
import collections
import datetime
import bson
import logging
import threading
import time
import random
import os
import importlib
logger = logging.getLogger(APP_NAME)

class TaskRunner:
    def __init__(self):
        self._last_run = None

    def random_sleep(self):
        time.sleep(random.randint(0, 50) / 1000.)

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('task')

    def run_task(self, task):
        self.random_sleep()
        thread = threading.Thread(target=task.run)
        thread.daemon = True
        thread.start()

    def run_thread(self):
        while True:
            cur_time = datetime.datetime.utcnow()

            if cur_time.minute != self._last_run:
                self._last_run = cur_time.minute

                for hour in ('all', cur_time.hour):
                    for task_cls in _tasks[hour][cur_time.minute]:
                        task = task_cls()
                        self.run_task(task)

            time.sleep(30)

    def check_thread(self):
        while True:
            cur_timestamp = datetime.datetime.utcnow()
            spec = {
                'ttl_timestamp': {'$lt': cur_timestamp},
            }

            for task_item in Task.iter_tasks(spec):
                self.random_sleep()

                response = Task.collection.update({
                    '_id': bson.ObjectId(task_item.id),
                    'ttl_timestamp': {'$lt': cur_timestamp},
                }, {'$unset': {
                    'runner_id': '',
                }})
                if response['updatedExisting']:
                    self.run_task(task_item)

            time.sleep(settings.mongo.task_ttl)

    def start(self):
        for module_name in os.listdir(os.path.dirname(__file__)):
            if module_name == '__init__.py' or \
                    module_name == 'runner.py' or \
                    module_name[-3:] != '.py':
                continue

            module_name = module_name[:-3]
            cls_name = 'Task' + ''.join([x.capitalize()
                for x in module_name.split('_')])
            module = __import__('pritunl.task.' + module_name,
                fromlist=(cls_name,))

        for target in (self.run_thread, self.check_thread):
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
