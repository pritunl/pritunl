from pritunl.constants import *
from pritunl.helpers import *
from pritunl import event
from pritunl import organization
from pritunl import queue

@queue.add_queue
class QueueInitOrgPooled(queue.Queue):
    fields = {
        'org_doc',
    } | queue.Queue.fields
    cpu_type = NORMAL_CPU
    type = 'init_org_pooled'

    def __init__(self, org_doc=None, **kwargs):
        queue.Queue.__init__(self, **kwargs)

        if org_doc is not None:
            self.org_doc = org_doc

        self.reserve_id = ORG_DEFAULT

    @cached_property
    def org(self):
        org = organization.Organization(doc=self.org_doc)
        org.exists = False
        return org

    def task(self):
        self.org.initialize(queue_user_init=False)
        self.load()

        if self.reserve_data:
            for field, value in list(self.reserve_data.items()):
                setattr(self.org, field, value)
        self.org.commit()

    def repeat_task(self):
        event.Event(type=ORGS_UPDATED)

    def pause_task(self):
        if self.reserve_data:
            return False
        self.load()
        if self.reserve_data:
            return False

        self.org.queue_com.running.clear()
        self.org.queue_com.popen_kill_all()

        return True

    def resume_task(self):
        self.org.queue_com.running.set()

@queue.add_reserve('queued_org')
def reserve_queued_org(name=None, auth_api=None, type=None, block=False):
    reserve_data = {}

    if name is not None:
        reserve_data['name'] = name
    if auth_api is not None:
        reserve_data['auth_api'] = auth_api
    if type is not None:
        reserve_data['type'] = type

    doc = QueueInitOrgPooled.reserve(type, reserve_data, block=block)
    if not doc:
        return

    doc = doc['org_doc']
    doc.update(reserve_data)

    return organization.Organization(doc=doc)
