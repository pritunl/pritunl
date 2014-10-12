from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *

import collections

channels = collections.defaultdict(set)

def add_listener(channel, callback):
    channels[channel].add(callback)
