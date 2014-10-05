from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import mongo

import collections

channels = collections.defaultdict(set)

def add_listener(channel, callback):
    channels[channel].add(callback)
