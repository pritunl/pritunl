from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.queue import Queue, add_queue
from pritunl.queue_com import QueueCom
from pritunl.event import Event
from pritunl import app_server
import pritunl.logger as logger
import pritunl.mongo as mongo
import pritunl.utils as utils
import os
import bson

class QueueDhParams(Queue):
    fields = {
        'server_id',
        'dh_param_bits',
    } | Queue.fields
    cpu_type = HIGH_CPU
    type = 'dh_params'

    def __init__(self, server_id=None, dh_param_bits=None, **kwargs):
        Queue.__init__(self, **kwargs)
        self.queue_com = QueueCom()

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

    @cached_property
    def server(self):
        from pritunl.server import Server
        return Server(doc=self.server_doc)

    def task(self):
        logger.debug('Generating server dh params', 'server',
            queue_id=self.id,
            dh_param_bits=self.dh_param_bits,
        )

        temp_path = app_server.get_temp_path()
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

        if not self.server_id:
            self.load()
            if self.reserve_data:
                self.server_id = self.reserve_data['server_id']

        if self.server_id:
            response = self.server_collection.update({
                '_id': bson.ObjectId(self.server_id),
                'dh_param_bits': self.dh_param_bits,
            }, {'$set': {
                'dh_params': self.dh_params,
            }})

            if response['updatedExisting']:
                logger.debug('Reserved queued server dh params', 'server',
                    queue_id=self.id,
                    dh_param_bits=self.dh_param_bits,
                )

                Event(type=SERVERS_UPDATED)
                return

        logger.debug('Adding pooled server dh params', 'server',
            queue_id=self.id,
            dh_param_bits=self.dh_param_bits,
        )

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

        logger.debug('Pausing queued dh params', 'server',
            queue_id=self.id,
            dh_param_bits=self.dh_param_bits,
        )

        self.queue_com.popen_kill_all()
        return True

    def repeat_task(self):
        Event(type=SERVERS_UPDATED)

    @classmethod
    def reserve_queued_dh_param(cls, server, block=False):
        from pritunl.server import Server

        reserve_id = server.dh_param_bits
        reserve_data = {
            'server_id': server.id,
        }

        doc = cls.reserve(reserve_id, reserve_data, block=block)
        if not doc:
            logger.debug('Reserved queued dh params', 'server',
                queue_id=str(doc['_id']),
                dh_param_bits=doc['dh_param_bits'],
            )
            return

        if block:
            server.load()

        return server

add_queue(QueueDhParams)
