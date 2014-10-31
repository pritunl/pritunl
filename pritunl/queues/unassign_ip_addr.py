from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import logger
from pritunl import mongo
from pritunl import server
from pritunl import queue

@queue.add_queue
class QueueUnassignIpAddr(queue.Queue):
    fields = {
        'server_id',
        'org_id',
        'user_id',
    } | queue.Queue.fields
    type = 'unassign_ip_addr'

    def __init__(self, server_id=None,
            org_id=None, user_id=None, **kwargs):
        queue.Queue.__init__(self, **kwargs)

        if server_id is not None:
            self.server_id = server_id
        if org_id is not None:
            self.org_id = org_id
        if user_id is not None:
            self.user_id = user_id

    def task(self):
        svr = server.get_by_id(self.server_id)
        if not svr:
            return

        for _ in xrange(5):
            if svr.network_lock:
                time.sleep(2)
                svr.load()
            else:
                break

        if svr.network_lock:
            raise ServerNetworkLocked('Server network is locked', {
                'server_id': svr.id,
                'queue_id': self.id,
                'queue_type': self.type,
            })

        svr.ip_pool.unassign_ip_addr(self.org_id, self.user_id)
