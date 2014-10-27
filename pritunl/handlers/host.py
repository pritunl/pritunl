from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import app
from pritunl import host
from pritunl import utils
from pritunl import logger
from pritunl import event
from pritunl import auth

import flask
import math
import time
import collections

@app.app.route('/host', methods=['GET'])
@app.app.route('/host/<host_id>', methods=['GET'])
@auth.session_auth
def host_get(host_id=None):
    if host_id:
        return utils.jsonify(host.get_host(id=host_id).dict())

    hosts = []

    for hst in host.iter_servers_dict():
        hosts.append(hst)

    return utils.jsonify(hosts)

@app.app.route('/host/<host_id>', methods=['PUT'])
@auth.session_auth
def host_put(host_id=None):
    hst = host.get_host(id=host_id)

    if 'name' in flask.request.json:
        hst.name = utils.filter_str(
            flask.request.json['name']) or utils.random_name()

    if 'public_address' in flask.request.json:
        hst.public_address = utils.filter_str(
            flask.request.json['public_address'])

    if 'link_address' in flask.request.json:
        hst.link_address = utils.filter_str(
            flask.request.json['link_address'])

    hst.commit(hst.changed)
    event.Event(type=HOSTS_UPDATED)

    return utils.jsonify(hst.dict())

@app.app.route('/host/<host_id>', methods=['DELETE'])
@auth.session_auth
def host_delete(host_id):
    hst = host.get_host(id=host_id)
    hst.remove()

    logger.LogEntry(message='Deleted host "%s".' % hst.name)
    event.Event(type=HOSTS_UPDATED)

    return utils.jsonify({})

@app.app.route('/host/<host_id>/usage/<period>', methods=['GET'])
@auth.session_auth
def host_usage_get(host_id, period):
    hst = host.get_host(id=host_id)
    return utils.jsonify(hst.usage.get_period(period))
