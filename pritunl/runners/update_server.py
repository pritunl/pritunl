from pritunl.helpers import *
from pritunl import app

import threading

@interrupter
def _update_server_thread():
    while True:
        app.update_server()
        yield interrupter_sleep(3)

def start_update_server():
    threading.Thread(target=_update_server_thread).start()
