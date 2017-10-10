from pritunl.server.output import ServerOutput

from pritunl.constants import *
from pritunl.helpers import *
from pritunl import mongo
from pritunl import event
from pritunl import utils

class ServerOutputLink(ServerOutput):
    @cached_static_property
    def collection(cls):
        return mongo.get_collection('servers_output_link')

    def send_event(self, link_server_ids, delay=True):
        if delay:
            delay = SERVER_OUTPUT_DELAY
        else:
            delay = None

        event.Event(
            type=SERVER_LINK_OUTPUT_UPDATED,
            resource_id=self.server_id,
            delay=delay,
        )
        for link_server_id in link_server_ids:
            if self.server_id != link_server_id:
                event.Event(
                    type=SERVER_LINK_OUTPUT_UPDATED,
                    resource_id=link_server_id,
                    delay=delay,
                )

    def clear_output(self, link_server_ids):
        self.collection.remove({
            'server_id': self.server_id,
        })
        self.send_event(link_server_ids, delay=False)

    def push_output(self, output, label, link_server_id):
        if self.server_id != link_server_id:
            server_ids = [self.server_id, link_server_id]
        else:
            server_ids = [self.server_id]

        self.collection.insert({
            'server_id': server_ids,
            'timestamp': utils.now(),
            'output': '[%s] %s' % (label, output.rstrip('\n')),
        })

        self.prune_output()
        self.send_event((link_server_id,))
