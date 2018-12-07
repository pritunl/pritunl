from pritunl.constants import *
from pritunl import app
from pritunl import host
from pritunl import utils
from pritunl import logger
from pritunl import event
from pritunl import auth
from pritunl import messenger
from pritunl import ipaddress
from pritunl import server
from pritunl import settings

import flask

@app.app.route('/host', methods=['GET'])
@app.app.route('/host/<hst>', methods=['GET'])
@auth.session_auth
def host_get(hst=None):
    if settings.app.demo_mode:
        resp = utils.demo_get_cache()
        if resp:
            return utils.jsonify(resp)

    if hst:
        resp = host.get_by_id(hst).dict()
        if settings.app.demo_mode:
            utils.demo_set_cache(resp)
        return utils.jsonify(resp)

    hosts = []
    page = flask.request.args.get('page', None)
    page = int(page) if page else page

    for hst in host.iter_hosts_dict(page=page):
        if settings.app.demo_mode:
            hst['users_online'] = hst['user_count']
        hosts.append(hst)

    if page is not None:
        resp = {
            'page': page,
            'page_total': host.get_host_page_total(),
            'hosts': hosts,
        }
    else:
        resp = hosts

    if settings.app.demo_mode:
        utils.demo_set_cache(resp)
    return utils.jsonify(resp)

@app.app.route('/host/<hst>', methods=['PUT'])
@auth.session_auth
def host_put(hst=None):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    hst = host.get_by_id(hst)

    if 'name' in flask.request.json:
        hst.name = utils.filter_str(
            flask.request.json['name']) or utils.random_name()

    if 'public_address' in flask.request.json:
        public_address = utils.filter_str(
            flask.request.json['public_address'])
        hst.public_address = public_address

    if 'public_address6' in flask.request.json:
        public_address6 = utils.filter_str(
            flask.request.json['public_address6'])
        hst.public_address6 = public_address6

    if 'routed_subnet6' in flask.request.json:
        routed_subnet6 = flask.request.json['routed_subnet6']
        if routed_subnet6:
            try:
                routed_subnet6 = ipaddress.IPv6Network(
                    flask.request.json['routed_subnet6'])
            except (ipaddress.AddressValueError, ValueError):
                return utils.jsonify({
                    'error': IPV6_SUBNET_INVALID,
                    'error_msg': IPV6_SUBNET_INVALID_MSG,
                }, 400)

            if routed_subnet6.prefixlen > 64:
                return utils.jsonify({
                    'error': IPV6_SUBNET_SIZE_INVALID,
                    'error_msg': IPV6_SUBNET_SIZE_INVALID_MSG,
                }, 400)

            routed_subnet6 = str(routed_subnet6)
        else:
            routed_subnet6 = None

        if hst.routed_subnet6 != routed_subnet6:
            if server.get_online_ipv6_count():
                return utils.jsonify({
                    'error': IPV6_SUBNET_ONLINE,
                    'error_msg': IPV6_SUBNET_ONLINE_MSG,
                }, 400)
            hst.routed_subnet6 = routed_subnet6

    if 'proxy_ndp' in flask.request.json:
        proxy_ndp = True if flask.request.json['proxy_ndp'] else False
        hst.proxy_ndp = proxy_ndp

    if 'local_address' in flask.request.json:
        local_address = utils.filter_str(
            flask.request.json['local_address'])
        hst.local_address = local_address

    if 'local_address6' in flask.request.json:
        local_address6 = utils.filter_str(
            flask.request.json['local_address6'])
        hst.local_address6 = local_address6

    if 'link_address' in flask.request.json:
        link_address = utils.filter_str(
            flask.request.json['link_address'])
        hst.link_address = link_address

    if 'sync_address' in flask.request.json:
        sync_address = utils.filter_str(
            flask.request.json['sync_address'])
        hst.sync_address = sync_address

    if 'availability_group' in flask.request.json:
        hst.availability_group = utils.filter_str(
            flask.request.json['availability_group']) or DEFAULT

    hst.commit(hst.changed)
    event.Event(type=HOSTS_UPDATED)
    messenger.publish('hosts', 'updated')

    return utils.jsonify(hst.dict())

@app.app.route('/host/<hst>', methods=['DELETE'])
@auth.session_auth
def host_delete(hst):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    hst = host.get_by_id(hst)
    hst.remove()

    logger.LogEntry(message='Deleted host "%s".' % hst.name)
    event.Event(type=HOSTS_UPDATED)

    return utils.jsonify({})

@app.app.route('/host/<hst>/usage/<period>', methods=['GET'])
@auth.session_auth
def host_usage_get(hst, period):
    if settings.app.demo_mode:
        resp = utils.demo_get_cache()
        if resp:
            return utils.jsonify(resp)

    hst = host.get_by_id(hst)

    if settings.app.demo_mode:
        resp = hst.usage.get_period_random(period)
        utils.demo_set_cache(resp)
    else:
        resp = hst.usage.get_period(period)
    return utils.jsonify(resp)
