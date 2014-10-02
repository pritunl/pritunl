from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import listener

def setup_listener():
    listener.start()
