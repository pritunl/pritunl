from constants import *
from exceptions import *
from descriptors import *
from mongo_object import MongoObject
from task import Task, _tasks
import mongo
import pymongo
import collections
import datetime
import bson
import logging
import threading
import time
import random
logger = logging.getLogger(APP_NAME)

class TaskRunner:
    def __init__(self):
        self._last_run = None

    def random_sleep(self):
        time.sleep(random.randint(0, 50) / 1000.)

    @static_property
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
                    for TaskClass in _tasks[hour][cur_time.minute]:
                        task = TaskClass()
                        self.run_task(task)

                for hour in ('all', cur_time.hour):
                    for TaskClass in _tasks[hour][cur_time.minute]:
                        task = TaskClass()
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

                self.run_task(task_item)

            time.sleep(MONGO_TASK_TTL)

    def start(self):
        from task_test import TaskTest

        thread = threading.Thread(target=self.run_thread)
        thread.daemon = True
        thread.start()

        thread = threading.Thread(target=self.check_thread)
        thread.daemon = True
        thread.start()
