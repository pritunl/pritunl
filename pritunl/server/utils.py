from pritunl.server.server import Server

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *

import uuid
import os
import signal
import time
import datetime
import subprocess
import threading
import traceback
import re
import json
import bson

def new_server(**kwargs):
    server = Server(**kwargs)
    server.initialize()
    return server

def get_server(id, fields=None):
    return Server(id=id, fields=fields)

def get_used_resources(ignore_server_id):
    used_resources = Server.collection.aggregate([
        {'$match': {
            '_id': {'$ne': bson.ObjectId(ignore_server_id)},
        }},
        {'$project': {
            'network': True,
            'interface': True,
            'port_protocol': {'$concat': [
                {'$substr': ['$port', 0, 5]},
                '$protocol',
            ]},
        }},
        {'$group': {
            '_id': None,
            'networks': {'$addToSet': '$network'},
            'interfaces': {'$addToSet': '$interface'},
            'ports': {'$addToSet': '$port_protocol'},
        }},
    ])['result']

    if not used_resources:
        used_resources = {
            'networks': set(),
            'interfaces': set(),
            'ports': set(),
        }
    else:
        used_resources = used_resources[0]
        used_resources.pop('_id')

    return {key: set(val) for key, val in used_resources.items()}

def iter_servers(fields=None):
    if fields:
        fields = {key: True for key in fields}
    for doc in Server.collection.find({}, fields).sort('name'):
        yield Server(doc=doc)
