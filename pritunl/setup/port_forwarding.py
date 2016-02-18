from pritunl import listener

def setup_port_forwarding():
    from pritunl import clients
    listener.add_listener('port_forwarding', clients.on_port_forwarding)
    listener.add_listener('client', clients.on_client)
