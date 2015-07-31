from pritunl import server
from pritunl import listener

def start_instance():
    listener.add_listener('instance', server.on_msg)
