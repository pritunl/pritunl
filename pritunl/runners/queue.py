from pritunl.constants import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import logger
from pritunl import listener
from pritunl import utils
from pritunl import queue
from pritunl import queues

import threading
import time

running_queues = {}
runner_queues = [utils.PyPriorityQueue() for _ in range(3)]
thread_limits = [threading.Semaphore(x) for x in (
    settings.app.queue_low_thread_limit,
    settings.app.queue_med_thread_limit,
    settings.app.queue_high_thread_limit,
)]

def add_queue_item(queue_item):
    if queue_item.id in running_queues:
        return
    running_queues[queue_item.id] = queue_item

    runner_queues[queue_item.cpu_type].put((
        abs(queue_item.priority - 4),
        queue_item,
    ))

    if queue_item.priority >= NORMAL:
        for running_queue in list(running_queues.values()):
            if running_queue.priority >= queue_item.priority:
                continue

            if running_queue.pause():
                runner_queues[running_queue.cpu_type].put((
                    abs(running_queue.priority - 4),
                    running_queue,
                ))
                thread_limits[running_queue.cpu_type].release()

def _on_msg(msg):
    try:
        if msg['message'][0] == PENDING:
            add_queue_item(queue.get(doc=msg['queue_doc']))
        elif msg['message'][0] == STOP:
            que = running_queues.get(msg['message'][1])
            if que:
                que.stop()
    except TypeError:
        pass

def run_timeout_queues():
    cur_timestamp = utils.now()
    spec = {
        'ttl_timestamp': {'$lt': cur_timestamp},
    }

    for queue_item in queue.iter_queues(spec):
        response = queue.Queue.collection.update({
            '_id': queue_item.id,
            'ttl_timestamp': {'$lt': cur_timestamp},
        }, {'$unset': {
            'runner_id': '',
        }})

        if response['updatedExisting']:
            runner_queues[queue_item.cpu_type].put((
                abs(queue_item.priority - 4),
                queue_item,
            ))

@interrupter
def _check_thread():
    while True:
        try:
            run_timeout_queues()
        except GeneratorExit:
            raise
        except:
            logger.exception('Error in queue check thread', 'runners')

        yield interrupter_sleep(settings.mongo.queue_ttl)

def run_queue_item(queue_item, thread_limit):
    release = True
    try:
        if queue_item.queue_com.state == None:
            queue_item.run()
        elif queue_item.queue_com.state == PAUSED:
            release = False
            queue_item.resume()
    finally:
        running_queues.pop(queue_item.id, None)
        if release:
            thread_limit.release()

def _runner_thread(cpu_priority, thread_limit, runner_queue):
    while True:
        try:
            thread_limit.acquire()
            priority, queue_item = runner_queue.get()

            thread = threading.Thread(target=run_queue_item,
                args=(queue_item, thread_limit))
            thread.daemon = True
            thread.start()
        except:
            logger.exception('Error in runner thread', 'runners')
            time.sleep(0.5)

def start_queue():
    for cpu_priority in (LOW_CPU, NORMAL_CPU, HIGH_CPU):
        thread = threading.Thread(target=_runner_thread, args=(
            cpu_priority,
            thread_limits[cpu_priority],
            runner_queues[cpu_priority],
        ))
        thread.daemon = True
        thread.start()

    threading.Thread(target=_check_thread).start()

    listener.add_listener('queue', _on_msg)
