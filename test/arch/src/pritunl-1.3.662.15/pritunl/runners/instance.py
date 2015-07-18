from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import server
from pritunl import listener

def start_instance():
    listener.add_listener('instance', server.on_msg)
