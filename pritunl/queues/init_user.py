from pritunl.constants import *
from pritunl.helpers import *
from pritunl import event
from pritunl import organization
from pritunl import user
from pritunl import queue

@queue.add_queue
class QueueInitUser(queue.Queue):
    fields = {
        'org_doc',
        'user_doc',
    } | queue.Queue.fields
    cpu_type = NORMAL_CPU
    type = 'init_user'

    def __init__(self, org_doc=None, user_doc=None, **kwargs):
        queue.Queue.__init__(self, **kwargs)

        if org_doc is not None:
            self.org_doc = org_doc
        if user_doc is not None:
            self.user_doc = user_doc

    @cached_property
    def org(self):
        return organization.Organization(doc=self.org_doc)

    @cached_property
    def user(self):
        usr = user.User(org=self.org, doc=self.user_doc)
        usr.exists = False
        return usr

    def task(self):
        self.user.initialize()
        self.user.commit()

    def repeat_task(self):
        event.Event(type=ORGS_UPDATED)
        event.Event(type=USERS_UPDATED, resource_id=self.org.id)
        event.Event(type=SERVERS_UPDATED)
