from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.queue import Queue
import pritunl.logger as logger
import pritunl.mongo as mongo
import pymongo
import random
import bson
import datetime
import logging
import threading
import time
import bson
import collections
from Queue import PriorityQueue

running_queues = {}
runner_queues = [PriorityQueue() for _ in xrange(3)]
thread_limits = [threading.Semaphore(x) for x in (4, 2, 1)]

class QueueRunner(object):
    def run_queue_item(self, queue_item):
        def pause():
            for running_queue in running_queues.values():
                if running_queue.priority >= queue_item.priority:
                    continue

                if running_queue.pause():
                    logger.debug('Puase queue item', 'queue',
                        queue_id=running_queue.id,
                        queue_type=running_queue.type,
                        queue_priority=running_queue.priority,
                        queue_cpu_type=running_queue.cpu_type,
                    )

                    runner_queues[running_queue.cpu_type].put((
                        abs(running_queue.priority - 4),
                        running_queue,
                    ))
                    thread_limits[running_queue.cpu_type].release()

        if queue_item.id in running_queues:
            return
        running_queues[queue_item.id] = queue_item

        logger.debug('Add queue item for run', 'queue',
            queue_id=queue_item.id,
            queue_type=queue_item.type,
            queue_priority=queue_item.priority,
            queue_cpu_type=queue_item.cpu_type,
        )

        runner_queues[queue_item.cpu_type].put((
            abs(queue_item.priority - 4),
            queue_item,
        ))

        if queue_item.priority >= NORMAL:
            thread = threading.Thread(target=pause)
            thread.daemon = True
            thread.start()

    def run_waiting_queues(self):
        spec = {
            'runner_id': {'$exists': False},
        }

        for queue_item in Queue.iter_queues(spec):
            self.run_queue_item(queue_item)

    def on_queue_msg(self, msg):
        try:
            if msg['message'][0] == PENDING:
                self.run_waiting_queues()
        except TypeError:
            pass

    def run_timeout_queues(self):
        cur_timestamp = datetime.datetime.utcnow()
        spec = {
            'ttl_timestamp': {'$lt': cur_timestamp},
        }

        for queue_item in Queue.iter_queues(spec):
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

    def runner_thread(self, cpu_priority, thread_limit, runner_queue):
        def run(queue_item):
            release = True
            try:
                if queue_item.queue_com.state == None:
                    logger.debug('Run queue item', 'queue_runner')
                    queue_item.run()
                elif queue_item.queue_com.state == PAUSED:
                    release = False
                    queue_item.resume()
            finally:
                running_queues.pop(queue_item.id, None)
                if release:
                    thread_limit.release()

        while True:
            thread_limit.acquire()
            priority, queue_item = runner_queue.get()

            thread = threading.Thread(target=run, args=(queue_item,))
            thread.daemon = True
            thread.start()

    def start(self):
        for cpu_priority in (LOW_CPU, NORMAL_CPU, HIGH_CPU):
            thread = threading.Thread(target=self.runner_thread, args=(
                cpu_priority,
                thread_limits[cpu_priority],
                runner_queues[cpu_priority],
            ))
            thread.daemon = True
            thread.start()

        for target in (self.watch_thread, self.check_thread):
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
