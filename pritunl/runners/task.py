from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import settings
from pritunl import mongo
from pritunl import logger
from pritunl import task

import pymongo
import collections
import datetime
import bson
import threading
import time
import random
import os
import importlib

def random_sleep():
    time.sleep(random.randint(0, 50) / 1000.)

def run_task(tsk):
    random_sleep()
    thread = threading.Thread(target=tsk.run)
    thread.daemon = True
    thread.start()

def run_thread():
    last_run = None

    while True:
        cur_time = datetime.datetime.utcnow()

        if cur_time.minute != last_run:
            last_run = cur_time.minute

            for hour in ('all', cur_time.hour):
                for task_cls in task.tasks[hour][cur_time.minute]:
                    tsk = task_cls()
                    run_task(tsk)

        time.sleep(30)

def check_thread():
    collection = mongo.get_collection('task')

    while True:
        cur_timestamp = datetime.datetime.utcnow()
        spec = {
            'ttl_timestamp': {'$lt': cur_timestamp},
        }

        for task_item in task.iter_tasks(spec):
            random_sleep()

            response = task.Task.collection.update({
                '_id': bson.ObjectId(task_item.id),
                'ttl_timestamp': {'$lt': cur_timestamp},
            }, {'$unset': {
                'runner_id': '',
            }})
            if response['updatedExisting']:
                run_task(task_item)

        time.sleep(settings.mongo.task_ttl)

def start_task():
    from pritunl import tasks

    for target in (run_thread, check_thread):
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
