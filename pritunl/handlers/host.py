from pritunl.event import Event
from pritunl.logger.entry import LogEntry
from pritunl.server.ip_pool import ServerIpPool

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl.app_server import app_server
from pritunl import host
from pritunl import utils

import flask
import math
import time
import collections

@app_server.app.route('/host', methods=['GET'])
@app_server.app.route('/host/<host_id>', methods=['GET'])
@app_server.auth
def host_get(host_id=None):
    if host_id:
        return utils.jsonify(host.get_host(id=host_id).dict())

    hosts = []

    for hst in host.iter_hosts():
        hosts.append(hst.dict())

    return utils.jsonify(hosts)

@app_server.app.route('/host/<host_id>', methods=['PUT'])
@app_server.auth
def host_put(host_id=None):
    hst = host.get_host(id=host_id)

    if 'name' in flask.request.json:
        hst.name = utils.filter_str(
            flask.request.json['name']) or utils.random_name()

    if 'public_address' in flask.request.json:
        hst.public_address = utils.filter_str(
            flask.request.json['public_address'])

    hst.commit(hst.changed)
    Event(type=HOSTS_UPDATED)

    return utils.jsonify(host.dict())

@app_server.app.route('/host/<host_id>', methods=['DELETE'])
@app_server.auth
def host_delete(host_id):
    hst = host.get_host(id=host_id)
    hst.remove()

    LogEntry(message='Deleted host "%s".' % hst.name)
    Event(type=HOSTS_UPDATED)

    return utils.jsonify({})

@app_server.app.route('/host/<host_id>/usage/<period>', methods=['GET'])
@app_server.auth
def host_usage_get(host_id, period):
    hst = host.get_host(id=host_id)
    return utils.jsonify(hst.usage.get_period(period))
