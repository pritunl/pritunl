from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.settings import settings
from pritunl.host import Host
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

    hosts = []

    for host in Host.iter_hosts():
        hosts.append(host.dict())

    return utils.jsonify(hosts)

@app_server.app.route('/host/<host_id>', methods=['PUT'])
@app_server.auth
def host_put(host_id=None):
    host = Host.get_host(id=host_id)

    host.name = utils.filter_str(
        flask.request.json['name']) or utils.random_name()
    host.commit()
    Event(type=HOSTS_UPDATED)

    return utils.jsonify(host.dict())

@app_server.app.route('/host/<host_id>', methods=['DELETE'])
@app_server.auth
def host_delete(host_id):
    host = Host.get_host(id=host_id)
    host.remove()

    LogEntry(message='Deleted host "%s".' % host.name)
    Event(type=HOSTS_UPDATED)

    return utils.jsonify({})
