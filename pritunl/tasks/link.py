from pritunl import settings
from pritunl import task
from pritunl import link

import collections

class TaskLink(task.Task):
    type = 'link'

    def task(self):
        if settings.app.demo_mode:
            return

        hosts = []
        location_available_hosts = collections.defaultdict(list)
        best_hosts = {}
        for hst in link.iter_hosts():
            hosts.append(hst)

            if not hst.is_available:
                continue

            location_available_hosts[hst.location_id].append(hst)

            cur_hst = best_hosts.get(hst.location_id)
            if not cur_hst:
                best_hosts[hst.location_id] = hst
                continue

            if hst.priority > cur_hst.priority:
                best_hosts[hst.location_id] = hst
                continue

            if hst.priority == cur_hst.priority and \
                    hst.active and not cur_hst.active:
                best_hosts[hst.location_id] = hst
                continue

        for hst in list(best_hosts.values()):
            if not hst.active:
                hst.set_active()

        for hst in hosts:
            hst.update_available(location_available_hosts[hst.location_id])

task.add_task(TaskLink, seconds=range(0, 60, 3))
