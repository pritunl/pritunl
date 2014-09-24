from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.settings import settings
from pritunl.organization import Organization
from pritunl.event import Event
from pritunl.log_entry import LogEntry
from pritunl.server_ip_pool import ServerIpPool
import pritunl.utils as utils
from pritunl import app_server
import flask
import math
import time
import collections

@app_server.app.route('/host', methods=['GET'])
@app_server.app.route('/host/<host_id>', methods=['GET'])
@app_server.auth
def host_get(host_id=None):
    if host_id:
        return tils.jsonify(Host.get_host(id=host_id).dict())
    return utils.jsonify({})

@app_server.app.route('/host', methods=['POST'])
@app_server.app.route('/host/<host_id>', methods=['PUT'])
@app_server.auth
def host_put_post(host_id=None):
    if host_id:
        return tils.jsonify(Host.get_host(id=host_id).dict())
    return utils.jsonify({})

@app_server.app.route('/host/<host_id>', methods=['DELETE'])
@app_server.auth
def host_delete(org_id, user_id):
    return utils.jsonify({})
