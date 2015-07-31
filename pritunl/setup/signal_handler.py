from pritunl.helpers import *

import signal

def handle_exit(signum, frame):
    set_global_interrupt()

def setup_signal_handler():
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
