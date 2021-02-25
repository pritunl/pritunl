from pritunl.queues.init_user import QueueInitUser

from pritunl.constants import *
from pritunl import organization
from pritunl import queue
from pritunl import user

@queue.add_queue
class QueueInitUserPooled(QueueInitUser):
    type = 'init_user_pooled'

    def __init__(self, **kwargs):
        QueueInitUser.__init__(self, **kwargs)

        org_id = self.org_doc['_id']
        user_type = str(self.user_doc['type'])

        self.reserve_id = str(org_id) + '-' + {
            CERT_SERVER_POOL: CERT_SERVER,
            CERT_CLIENT_POOL: CERT_CLIENT,
        }[user_type]

    def task(self):
        self.user.initialize()
        self.load()

        if self.reserve_data:
            for field, value in list(self.reserve_data.items()):
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

@queue.add_reserve('queued_user')
def reserve_queued_user(org, name=None, email=None, pin=None, type=None,
        groups=None, auth_type=None, yubico_id=None, disabled=None,
        bypass_secondary=None, client_to_client=None, mac_addresses=None,
        dns_servers=None, dns_suffix=None, port_forwarding=None,
        resource_id=None, block=False):
    reserve_id = str(org.id) + '-' + type
    reserve_data = {}

    if name is not None:
        reserve_data['name'] = name
    if email is not None:
        reserve_data['email'] = email
    if pin is not None:
        reserve_data['pin'] = pin
    if type is not None:
        reserve_data['type'] = type
    if groups is not None:
        reserve_data['groups'] = groups
    if auth_type is not None:
        reserve_data['auth_type'] = auth_type
    if yubico_id is not None:
        reserve_data['yubico_id'] = yubico_id
    if disabled is not None:
        reserve_data['disabled'] = disabled
    if bypass_secondary is not None:
        reserve_data['bypass_secondary'] = bypass_secondary
    if client_to_client is not None:
        reserve_data['client_to_client'] = client_to_client
    if mac_addresses is not None:
        reserve_data['mac_addresses'] = mac_addresses
    if dns_servers is not None:
        reserve_data['dns_servers'] = dns_servers
    if dns_suffix is not None:
        reserve_data['dns_suffix'] = dns_suffix
    if port_forwarding is not None:
        reserve_data['port_forwarding'] = port_forwarding
    if resource_id is not None:
        reserve_data['resource_id'] = resource_id

    doc = QueueInitUserPooled.reserve(reserve_id, reserve_data, block=block)
    if not doc:
        return

    user_doc = doc['user_doc']
    user_doc.update(reserve_data)

    org = organization.Organization(doc=doc['org_doc'])
    return user.User(org=org, doc=user_doc)
