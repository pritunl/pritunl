from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *

def setup_queue_runner():
    from pritunl import queue
    queue.start_runner()
