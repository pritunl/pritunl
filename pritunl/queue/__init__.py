queue_types = {}

def add_queue(queue_cls):
    queue_types[queue_cls.type] = queue_cls
