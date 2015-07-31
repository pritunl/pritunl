from pritunl import settings
from pritunl import logger
from pritunl import server
from pritunl import listener

import time

def _on_msg(msg):
    if msg['message'] != 'start':
        return

    try:
        svr = server.get_by_id(msg['server_id'])
        if settings.local.host_id not in svr.hosts:
            return

        for instance in svr.instances:
            if instance['host_id'] == settings.local.host_id:
                return

        prefered_hosts = msg.get('prefered_hosts')

        if prefered_hosts and settings.local.host_id not in prefered_hosts:
            time.sleep(0.1)

        svr.run(send_events=msg.get('send_events'))
    except:
        logger.exception('Failed to run server', 'runners')

def start_server():
    listener.add_listener('servers', _on_msg)
