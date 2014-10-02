from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import host

def setup_host():
    host.init_host().keep_alive()
