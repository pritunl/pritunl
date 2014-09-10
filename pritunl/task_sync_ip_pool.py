from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.task import Task, add_task
from pritunl.server import Server
import logging
import time

logger = logging.getLogger(APP_NAME)

class TaskSyncIpPool(Task):
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

add_task(TaskSyncIpPool, minutes=0)
