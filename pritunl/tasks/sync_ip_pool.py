from pritunl import task
from pritunl import logger
from pritunl import server

class TaskSyncIpPool(task.Task):
    type = 'sync_ip_pool'

    def task(self):
        for svr in server.iter_servers():
            try:
                svr.ip_pool.sync_ip_pool()
            except:
                logger.exception('Failed to sync server IP pool', 'tasks',
                    server_id=svr.id,
                    task_id=self.id,
                )

task.add_task(TaskSyncIpPool, hours=4, minutes=7)
