from pritunl import pooler
from pritunl import task

class TaskPooler(task.Task):
    type = 'pooler'

    def task(self):
        pooler.fill('org')
        pooler.fill('user')
        pooler.fill('dh_params')

task.add_task(TaskPooler, minutes=range(0, 60, 5))
