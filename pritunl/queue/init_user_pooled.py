from pritunl.queue.init_user import QueueInitUser
from pritunl.queue import add_queue

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.app_server import app_server
from pritunl import logger

@add_queue
class QueueInitUserPooled(QueueInitUser):
    type = 'init_user_pooled'

    def __init__(self, **kwargs):
        QueueInitUser.__init__(self, **kwargs)

        org_id = str(self.org_doc['_id'])
        user_type = str(self.user_doc['type'])

        self.reserve_id = org_id + '-' + {
            CERT_SERVER_POOL: CERT_SERVER,
            CERT_CLIENT_POOL: CERT_CLIENT,
        }[user_type]

    def task(self):
        self.user.initialize()
        self.load()

        if self.reserve_data:
            for field, value in self.reserve_data.items():
                setattr(self.user, field, value)
        self.user.commit()

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

@reserve('queued_user')
def reserve_queued_user(org, name=None, email=None, type=None,
        disabled=None, block=False):
    from pritunl.user import User
    from pritunl.organization import Organization

    reserve_id = org.id + '-' + type
    reserve_data = {}

    if name is not None:
        reserve_data['name'] = name
    if email is not None:
        reserve_data['email'] = email
    if type is not None:
        reserve_data['type'] = type
    if disabled is not None:
        reserve_data['disabled'] = disabled

    doc = QueueInitUserPooled.reserve(reserve_id, reserve_data, block=block)
    if not doc:
        return

    org = Organization(doc=doc['org_doc'])
    return User(org=org, doc=doc['user_doc'])
