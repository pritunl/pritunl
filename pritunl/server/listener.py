_channels = {}

def add_listener(instance_id, callback):
    _channels[instance_id] = callback

def remove_listener(instance_id):
    _channels.pop(instance_id, None)

def on_msg(msg):
    for callback in list(_channels.values()):
        callback(msg)
