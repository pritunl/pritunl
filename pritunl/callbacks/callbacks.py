
_port_listeners = {}
_client_listeners = {}
_client_link_listeners = {}
_firewall_listeners = {}

def add_port_listener(instance_id, callback):
    _port_listeners[instance_id] = callback

def remove_port_listener(instance_id):
    _port_listeners.pop(instance_id, None)

def on_port_forwarding(msg):
    for listener in list(_port_listeners.values()):
        listener(
            msg['message']['org_id'],
            msg['message']['user_id'],
        )

def add_client_listener(instance_id, callback):
    _client_listeners[instance_id] = callback

def remove_client_listener(instance_id):
    _client_listeners.pop(instance_id, None)

def add_client_link_listener(instance_id, callback):
    _client_link_listeners[instance_id] = callback

def remove_client_link_listener(instance_id):
    _client_link_listeners.pop(instance_id, None)

def on_client(msg):
    for listener in list(_client_listeners.values()):
        listener(
            msg['message']['state'],
            msg['message'].get('server_id'),
            msg['message']['virt_address'],
            msg['message']['virt_address6'],
            msg['message']['host_address'],
            msg['message']['host_address6'],
        )

def on_client_link(msg):
    for listener in list(_client_link_listeners.values()):
        listener(
            msg['message']['state'],
            msg['message']['server_id'],
            msg['message']['virt_address'],
            msg['message']['virt_address6'],
            msg['message']['host_address'],
            msg['message']['host_address6'],
            msg['message']['network_links'],
        )

# Call in clients init
def add_firewall_listener(instance_id, callback):
    _firewall_listeners[instance_id] = callback

# Call on clients exit
def remove_firewall_listener(instance_id):
    _firewall_listeners.pop(instance_id, None)

def on_firewall_check(instance_id, client_id):
    listener = _firewall_listeners.get(instance_id)
    if listener:
        return listener(client_id)
    return False
