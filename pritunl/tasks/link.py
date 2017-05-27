from pritunl import settings
from pritunl import task
from pritunl import link

class TaskLink(task.Task):
    type = 'link'

    def task(self):
        if settings.app.demo_mode:
            return

        best_hosts = {}
        for hst in link.iter_hosts():
            if not hst.check_available():
                continue

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

        for hst in best_hosts.values():
            if not hst.active:
                hst.set_active()

task.add_task(TaskLink, seconds=xrange(0, 60, 3))
