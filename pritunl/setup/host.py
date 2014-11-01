from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *

def setup_host():
    from pritunl import host
    host.init()
