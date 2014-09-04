from constants import *
from exceptions import *
from descriptors import *
from queue import Queue
from messenger import Messenger
import mongo
import pymongo
import random
import bson
import datetime
import logging
import threading
import time

logger = logging.getLogger(APP_NAME)

class QueueRunner(object):
    def random_sleep(self):
        time.sleep(random.randint(0, 50) / 1000.)

    def watch_thread(self):
        messenger = Messenger('queue')
        while True:
            try:
                for msg in messenger.subscribe():
                    break

                spec = {
                    'runner_id': {'$exists': False},
                }
                for queue_item in Queue.iter_queues(spec):
                    self.random_sleep()
                    queue_item.run()
            except:
                logger.exception('Error in queue watch thread.')
                time.sleep(0.5)

    def check_thread(self):
        while True:
            try:
                spec = {
                    'ttl_timestamp': {'$lt': datetime.datetime.utcnow()},
                }
                for queue_item in Queue.iter_queues(spec):
                    Queue.collection.update({
                        '_id': bson.ObjectId(queue_item.id),
                    }, {'$unset': {
                        'runner_id': '',
                    }})

                    self.random_sleep()
                    queue_item.run()
            except:
                logger.exception('Error in queue check thread.')

            time.sleep(MONGO_QUEUE_TTL)

    def start(self):
        thread = threading.Thread(target=self.watch_thread)
        thread.daemon = True
        thread.start()

        thread = threading.Thread(target=self.check_thread)
        thread.daemon = True
        thread.start()
