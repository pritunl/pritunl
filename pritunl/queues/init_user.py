from pritunl.queue import Queue, add_queue

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.app_server import app_server
from pritunl import logger
from pritunl import event
from pritunl import organization

@add_queue
class QueueInitUser(Queue):
    fields = {
        'org_doc',
        'user_doc',
    } | Queue.fields
    cpu_type = NORMAL_CPU
    type = 'init_user'

    def __init__(self, org_doc=None, user_doc=None, **kwargs):
        Queue.__init__(self, **kwargs)

        if org_doc is not None:
            self.org_doc = org_doc
        if user_doc is not None:
            self.user_doc = user_doc

    @cached_property
    def org(self):
        return organization.Organization(doc=self.org_doc)

    @cached_property
    def user(self):
        from pritunl.user import User
        user = User(org=self.org, doc=self.user_doc)
        user.exists = False
        return user

    def task(self):
        self.user.initialize()
        self.user.commit()

    def repeat_task(self):
        event.Event(type=ORGS_UPDATED)
        event.Event(type=USERS_UPDATED, resource_id=self.org.id)
        event.Event(type=SERVERS_UPDATED)
