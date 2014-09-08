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

    def __init__(self, org_doc=None, user_doc=None, **kwargs):
        Queue.__init__(self, **kwargs)
        self.type = 'init_user'

        if org_doc is not None:
            self.org_doc = org_doc
        if user_doc is not None:
            self.user_doc = user_doc

    def task(self):
        from pritunl.user import User
        from pritunl.organization import Organization

        org = Organization(doc=self.org_doc)
        user = User(org=org, doc=self.user_doc)
        user.initialize()
        user.commit()

add_queue('init_user', QueueInitUser)
