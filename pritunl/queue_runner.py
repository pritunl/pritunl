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

logger = logging.getLogger(APP_NAME)

# TODO add queue threads

class QueueRunner(object):
    def random_sleep(self):
        time.sleep(random.randint(0, 10) / 1000.)

    def run_waiting_queues(self):
        spec = {
            'runner_id': {'$exists': False},
        }
        for queue_item in Queue.iter_queues(spec):
            self.random_sleep()
            queue_item.run()

    def watch_thread(self):
        messenger = Messenger('queue')
        while True:
            try:
                for msg in messenger.subscribe():
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
                queue_item.run()

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
