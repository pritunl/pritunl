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
running_queues = collections.defaultdict(set)
thread_limit = threading.Semaphore(MONGO_QUEUE_THREAD_LIMIT)

class QueueRunner(object):
    def random_sleep(self):
        time.sleep(random.randint(0, 10) / 1000.)

    def run_queue_item(self, queue_item):
        paused_queues = set()

        def pause():
            for queue_priority in xrange(min(NORMAL, queue_item.priority)):
                for running_queue in copy.copy(running_queues[queue_priority]):
                    if running_queue.pause():
                        paused_queues.add(running_queue)
                        thread_limit.release()

        thread = threading.Thread(target=pause)
        thread.daemon = True
        thread.start()

        def run():
            thread_limit.acquire()
            running_queues[queue_item.priority].add(queue_item)
            try:
                queue_item.run()
            finally:
                try:
                    running_queues[queue_item.priority].remove(queue_item)
                except KeyError:
                    pass
                thread_limit.release()

                for paused_queue in paused_queues:
                    thread_limit.acquire()
                    paused_queue.resume()

        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def run_waiting_queues(self):
        spec = {
            'runner_id': {'$exists': False},
        }
        for queue_item in Queue.iter_queues(spec):
            self.random_sleep()
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
