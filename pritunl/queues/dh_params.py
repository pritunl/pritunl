from pritunl.constants import *
from pritunl.helpers import *
from pritunl import mongo
from pritunl import utils
from pritunl import event
from pritunl import queue

import os

@queue.add_queue
class QueueDhParams(queue.Queue):
    fields = {
        'server_id',
        'dh_param_bits',
    } | queue.Queue.fields
    cpu_type = HIGH_CPU
    type = 'dh_params'

    def __init__(self, server_id=None, dh_param_bits=None, **kwargs):
        queue.Queue.__init__(self, **kwargs)
        self.queue_com = queue.QueueCom()

        if server_id is not None:
            self.server_id = server_id
        if dh_param_bits is not None:
            self.dh_param_bits = dh_param_bits

    @cached_static_property
    def dh_params_collection(cls):
        return mongo.get_collection('dh_params')

    @cached_static_property
    def server_collection(cls):
        return mongo.get_collection('servers')

    def task(self):
        self.queue_com.wait_status()

        temp_path = utils.get_temp_path()
        dh_param_path = os.path.join(temp_path, DH_PARAM_NAME)

        try:
            os.makedirs(temp_path)
            args = [
                'openssl', 'dhparam',
                '-out', dh_param_path,
                str(self.dh_param_bits),
            ]
            self.queue_com.popen(args)
            self.read_file('dh_params', dh_param_path)
        finally:
            utils.rmtree(temp_path)

        self.queue_com.wait_status()

        if not self.server_id:
            self.load()
            if self.reserve_data:
                self.server_id = self.reserve_data['server_id']

        if self.server_id:
            response = self.server_collection.update({
                '_id': self.server_id,
                'dh_param_bits': self.dh_param_bits,
            }, {'$set': {
                'dh_params': self.dh_params,
            }})

            if response['updatedExisting']:
                event.Event(type=SERVERS_UPDATED)
                return

        self.dh_params_collection.insert({
            'dh_param_bits': self.dh_param_bits,
            'dh_params': self.dh_params,
        })

    def pause_task(self):
        if self.reserve_data:
            return False
        self.load()
        if self.reserve_data:
            return False

        self.queue_com.running.clear()
        self.queue_com.popen_kill_all()

        return True

    def stop_task(self):
        self.queue_com.running.clear()
        self.queue_com.popen_kill_all()

        return True

    def resume_task(self):
        self.queue_com.running.set()

@queue.add_reserve('pooled_dh_params')
def reserve_pooled_dh_params(svr):
    doc = QueueDhParams.dh_params_collection.find_and_modify({
        'dh_param_bits': svr.dh_param_bits,
    }, {'$set': {
        'dh_param_bits': None,
    }}, new=True)

    if not doc:
        return False

    QueueDhParams.dh_params_collection.remove(doc['_id'])

    svr.dh_params = doc['dh_params']
    return True

@queue.add_reserve('queued_dh_params')
def reserve_queued_dh_params(svr, block=False):
    reserve_id = svr.dh_param_bits
    reserve_data = {
        'server_id': svr.id,
    }

    doc = QueueDhParams.reserve(reserve_id, reserve_data, block=block)
    if not doc:
        return False

    if block:
        svr.load()

    return True
