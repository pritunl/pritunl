from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.queue import Queue
from pritunl.messenger import Messenger
import pritunl.mongo as mongo
import pymongo
import random
import bson
import datetime
import logging
import threading
import time
import bson
import copy
import collections

logger = logging.getLogger(APP_NAME)
running_queues = collections.defaultdict(
    lambda: collections.defaultdict(set))
thread_limits = [
    threading.Semaphore(4),
    threading.Semaphore(2),
    threading.Semaphore(1),
]

class QueueRunner(object):
    def random_sleep(self):
        time.sleep(random.randint(0, 10) / 1000.)

    def run_queue_item(self, queue_item):
        queues = running_queues[queue_item.cpu_type][queue_item.priority]
        paused_queues = set()

        def pause():
            for queue_priority in xrange(min(NORMAL, queue_item.priority)):
                for running_queue in copy.copy(
                        running_queues[queue_item.cpu_type][queue_priority]):
                    if running_queue.pause():
                        paused_queues.add(running_queue)
                        thread_limits[queue_item.cpu_type].release()

        def run():
            thread_limits[queue_item.cpu_type].acquire()
            try:
                queue_item.run()
            finally:
                try:
                    running_queues[queue_item.cpu_type][
                        queue_item.priority].remove(queue_item.id)
                except KeyError:
                    pass

                thread_limits[queue_item.cpu_type].release()

                for paused_queue in paused_queues:
                    thread_limits[queue_item.cpu_type].acquire()
                    paused_queue.resume()

        if queue_item.id in queues:
            return
        queues.add(queue_item.id)

        thread = threading.Thread(target=pause)
        thread.daemon = True
        thread.start()

        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def run_waiting_queues(self):
        spec = {
            'runner_id': {'$exists': False},
        }
        self.random_sleep()
        for queue_item in Queue.iter_queues(spec):
            self.run_queue_item(queue_item)

    def watch_thread(self):
        messenger = Messenger()

        while True:
            try:
                for msg in messenger.subscribe('queue'):
                    try:
                        if msg['message'][0] == PENDING:
                            self.run_waiting_queues()
                    except TypeError:
                        pass
            except:
                logger.exception('Error in queue watch thread.')
                time.sleep(0.5)

    def run_timeout_queues(self):
        cur_timestamp = datetime.datetime.utcnow()
        spec = {
            'ttl_timestamp': {'$lt': cur_timestamp},
        }

        for queue_item in Queue.iter_queues(spec):
            self.random_sleep()

            response = Queue.collection.update({
                '_id': bson.ObjectId(queue_item.id),
                'ttl_timestamp': {'$lt': cur_timestamp},
            }, {'$unset': {
                'runner_id': '',
            }})
            if response['updatedExisting']:
                self.run_queue_item(queue_item)

    def check_thread(self):
        while True:
            try:
                self.run_timeout_queues()
            except:
                logger.exception('Error in queue check thread.')

            time.sleep(MONGO_QUEUE_TTL)

    def start(self):
        for target in (self.watch_thread, self.check_thread):
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
