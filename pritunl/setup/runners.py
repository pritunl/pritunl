from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *

def setup_runners():
    from pritunl import runners
    runners.start_all()
