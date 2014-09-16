from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.task import Task, add_task
from pritunl.pooler_user import PoolerUser
from pritunl.pooler_org import PoolerOrg
from pritunl.pooler_dh_params import PoolerDhParams
import logging
import time

logger = logging.getLogger(APP_NAME)

class TaskPooler(Task):
    type = 'pooler'

    def task(self):
        PoolerOrg.fill_pool()
        PoolerUser.fill_pool()
        PoolerDhParams.fill_pool()

add_task(TaskPooler, minutes=(0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55))
