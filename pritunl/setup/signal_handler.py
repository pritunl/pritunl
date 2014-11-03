from pritunl import __version__

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import logger

import signal

_exited = False

def handle_exit(signum, frame):
    global _exited
    if _exited:
        return
    _exited = True
    logger.info('Stopping server...')
    set_global_interrupt()
    signal.alarm(2)

def setup_signal_handler():
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
