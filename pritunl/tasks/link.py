from pritunl import settings
from pritunl import task
from pritunl import link

import collections

class TaskLink(task.Task):
    type = 'link'
    delay = 10

    def task(self):
        if settings.app.demo_mode:
            return

        hosts = []
        location_available_hosts = collections.defaultdict(list)
        for hst in link.iter_hosts():
            hosts.append(hst)

            if not hst.is_available:
                continue

            location_available_hosts[hst.location_id].append(hst)

        for hst in hosts:
            hst.update_available(location_available_hosts[hst.location_id])

task.add_task(TaskLink, seconds=range(0, 60, 3))
