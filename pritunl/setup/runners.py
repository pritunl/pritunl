from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *

def setup_runners():
    from pritunl import runners
    runners.start_all()
