from pritunl.server.output import ServerOutput
from pritunl.server.output_link import ServerOutputLink
from pritunl.server.bandwidth import ServerBandwidth
from pritunl.server.ip_pool import ServerIpPool
from pritunl.server.instance import ServerInstance
from pritunl.server.server import Server, dict_fields

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

def iter_servers_dict():
    fields = {key: True for key in dict_fields}
    for doc in Server.collection.find({}, fields).sort('name'):
        yield Server(doc=doc).dict()

def output_get(server_id):
    return ServerOutput(server_id).get_output()

def output_clear(server_id):
    ServerOutput(server_id).clear_output()

def output_link_get(server_id):
    return ServerOutputLink(server_id).get_output()

def output_link_clear(server_id):
    svr = get_server(id=server_id, fields=['_id', 'links'])
    ServerOutputLink(server_id).clear_output(svr.links.keys())

def bandwidth_get(server_id, period):
    return ServerBandwidth(server_id).get_period(period)
