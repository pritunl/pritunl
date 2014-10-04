from pritunl.server import Server

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import task
from pritunl import logger

import time

class TaskSyncIpPool(task.Task):
    type = 'sync_ip_pool'

    def task(self):
        for server in Server.iter_servers():
            try:
                server.ip_pool.sync_ip_pool()
            except:
                logger.exception('Failed to sync server IP pool. %r' % {
                    'server_id': server.id,
                    'task_id': self.id,
                })

task.add_task(TaskSyncIpPool, minutes=7)
