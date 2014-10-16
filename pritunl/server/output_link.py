from pritunl.server.output import ServerOutput

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import mongo
from pritunl import event

class ServerOutputLink(ServerOutput):
    @cached_static_property
    def collection(cls):
        return mongo.get_collection('servers_output_link')

    def send_event(self):
        event.Event(type=SERVER_LINK_OUTPUT_UPDATED,
            resource_id=self.server_id)
