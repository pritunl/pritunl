from pritunl import listener
from pritunl import callbacks

def setup_server_listeners():
    from pritunl import vxlan
    listener.add_listener('port_forwarding', callbacks.on_port_forwarding)
    listener.add_listener('client', callbacks.on_client)
    listener.add_listener('client_links', callbacks.on_client_link)
    listener.add_listener('vxlan', vxlan.on_vxlan)
