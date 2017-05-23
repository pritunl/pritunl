from pritunl import settings
from pritunl import task
from pritunl import link
from pritunl import utils

class TaskLink(task.Task):
    type = 'link'

    def task(self):
        if settings.app.demo_mode:
            return

        spec = {
            'ping_timestamp_ttl': {'$lt': utils.now()},
        }

        for hst in link.iter_hosts(spec):
            hst.check_available()

task.add_task(TaskLink, seconds=xrange(0, 60, 3))
