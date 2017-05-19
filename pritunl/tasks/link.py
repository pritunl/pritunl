from pritunl import settings
from pritunl import task
from pritunl import link

class TaskLink(task.Task):
    type = 'link'

    def task(self):
        if settings.app.demo_mode:
            return

        for hst in link.iter_hosts():
            hst.check_available()

task.add_task(TaskLink, seconds=xrange(0, 60, 3))
