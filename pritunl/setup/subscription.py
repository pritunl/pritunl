from pritunl import listener
from pritunl import subscription

def _on_msg(msg):
    if msg['message'] != 'updated':
        return
    subscription.update()

def setup_subscription():
    listener.add_listener('subscription', _on_msg)
