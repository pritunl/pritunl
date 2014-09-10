from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.queue import Queue, add_queue
from pritunl.event import Event
from pritunl import app_server
import logging

logger = logging.getLogger(APP_NAME)

class QueueInitUser(Queue):
    fields = {
        'org_doc',
        'user_doc',
    } | Queue.fields
    type = 'init_user'

    def __init__(self, org_doc=None, user_doc=None, **kwargs):
        Queue.__init__(self, **kwargs)

        if org_doc is not None:
            self.org_doc = org_doc
        if user_doc is not None:
            self.user_doc = user_doc

    @cached_property
    def user(self):
        from pritunl.user import User
        from pritunl.organization import Organization

        org = Organization(doc=self.org_doc)
        user = User(org=org, doc=self.user_doc)
        user.exists = False

        return user

    def task(self):
        self.user.initialize()
        self.user.commit()

    def repeat_task(self):
        Event(type=ORGS_UPDATED)
        Event(type=USERS_UPDATED, resource_id=self.org.id)
        Event(type=SERVERS_UPDATED)

add_queue('init_user', QueueInitUser)
