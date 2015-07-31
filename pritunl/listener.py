import collections

channels = collections.defaultdict(set)

def add_listener(channel, callback):
    channels[channel].add(callback)
