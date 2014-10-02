from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.task import Task, add_task
from pritunl import pooler
import logging
import time

logger = logging.getLogger(APP_NAME)

class TaskPooler(Task):
    type = 'pooler'

    def task(self):
        pooler.fill('org')
        pooler.fill('user')
        pooler.fill('dh_params')

add_task(TaskPooler, minutes=xrange(0, 60, 5))
