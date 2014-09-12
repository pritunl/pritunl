from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.queue import Queue, add_queue
from pritunl.event import Event
from pritunl import app_server
import logging

logger = logging.getLogger(APP_NAME)

class QueueInitOrgPooled(Queue):
    fields = {
        'org_doc',
    } | Queue.fields
    type = 'init_org_pooled'

    def __init__(self, org_doc=None, **kwargs):
        Queue.__init__(self, **kwargs)

        if org_doc is not None:
            self.org_doc = org_doc

        self.reserve_id = ORG_DEFAULT

    @cached_property
    def org(self):
        from pritunl.organization import Organization
        org = Organization(doc=self.org_doc)
        org.exists = False
        return org

    def task(self):
        self.org.initialize(queue_user_init=False)

    def repeat_task(self):
        Event(type=ORGS_UPDATED)

    def complete_task(self):
        self.load()
        if self.reserve_data:
            for field, value in self.reserve_data.items():
                setattr(self.org, field, value)
        self.org.commit()

    @classmethod
    def reserve_queued_org(cls, name=None, type=None, block=False):
        from pritunl.organization import Organization

        reserve_data = {}

        if name is not None:
            reserve_data['name'] = name
        if type is not None:
            reserve_data['type'] = type

        doc = cls.reserve(type, reserve_data, block=block)
        if not doc:
            return

        return Organization(doc=doc['org_doc'])

add_queue('init_org_pooled', QueueInitOrgPooled)
