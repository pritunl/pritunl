from pritunl import listener

def setup_server_listeners():
    from pritunl import clients
    from pritunl import vxlan
    listener.add_listener('port_forwarding', clients.on_port_forwarding)
    listener.add_listener('client', clients.on_client)
    listener.add_listener('vxlan', vxlan.on_vxlan)
