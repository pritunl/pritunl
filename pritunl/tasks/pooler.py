from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import pooler
from pritunl import task
from pritunl import logger

class TaskPooler(task.Task):
    type = 'pooler'

    def task(self):
        pooler.fill('org')
        pooler.fill('user')
        pooler.fill('dh_params')

task.add_task(TaskPooler, minutes=xrange(0, 60, 5))
