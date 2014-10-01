from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.task import Task, add_task
from pritunl.pooler.user import PoolerUser
from pritunl.pooler.org import PoolerOrg
from pritunl.pooler.dh_params import PoolerDhParams
from pritunl import pooler
import logging
import time

logger = logging.getLogger(APP_NAME)

class TaskPooler(Task):
    type = 'pooler'

    def task(self):
        PoolerOrg.fill_pool()
        PoolerUser.fill_pool()
        PoolerDhParams.fill_pool()

add_task(TaskPooler, minutes=xrange(0, 60, 5))
