from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import mongo
from pritunl import logger
from pritunl import task
from pritunl import utils

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

def print_tasks():
    for hour in task.tasks:
        print 'hour:', hour
        for minute in task.tasks[hour]:
            print '    minute:', minute
            for second in task.tasks[hour][minute]:
                print '        second:', second
                for tsk in task.tasks[hour][minute][second]:
                    print '            task:', tsk

@interrupter
def run_thread():
    last_run = None

    while True:
        cur_time = utils.now()

        if int(time.mktime(cur_time.timetuple())) != last_run:
            last_run = int(time.mktime(cur_time.timetuple()))

            for hour in ('all', cur_time.hour):
                for minute in ('all', cur_time.minute):
                    for second in ('all', cur_time.second):
                        for task_cls in task.tasks[hour][minute][second]:
                            run_task(task_cls())

        time.sleep(0.5)

        yield

@interrupter
def check_thread():
    collection = mongo.get_collection('task')

    while True:
        cur_timestamp = utils.now()
        spec = {
            'ttl_timestamp': {'$lt': cur_timestamp},
        }

        for task_item in task.iter_tasks(spec):
            random_sleep()

            response = task.Task.collection.update({
                '_id': task_item.id,
                'ttl_timestamp': {'$lt': cur_timestamp},
            }, {'$unset': {
                'runner_id': '',
            }})
            if response['updatedExisting']:
                run_task(task_item)

        yield interrupter_sleep(settings.mongo.task_ttl)

def start_task():
    from pritunl import tasks

    for target in (run_thread, check_thread):
        threading.Thread(target=target).start()
