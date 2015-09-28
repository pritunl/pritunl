from pritunl.constants import *
from pritunl import settings
from pritunl import utils
from pritunl import app
from pritunl import auth
from pritunl import event
from pritunl import ipaddress
from pritunl import server

import flask

@app.app.route('/settings', methods=['GET'])
@auth.session_auth
def settings_get():
    response = flask.g.administrator.dict()
    response.update({
        'theme': settings.app.theme,
        'email_from': settings.app.email_from,
        'email_server': settings.app.email_server,
        'email_username': settings.app.email_username,
        'email_password': bool(settings.app.email_password),
        'sso': settings.app.sso,
        'sso_match': settings.app.sso_match,
        'sso_token': settings.app.sso_token,
        'sso_secret': settings.app.sso_secret,
        'sso_host': settings.app.sso_host,
        'sso_admin': settings.app.sso_admin,
        'sso_org': settings.app.sso_org,
        'public_address': settings.local.host.public_addr,
        'public_address6': settings.local.host.public_addr6,
        'routed_subnet6': settings.local.host.routed_subnet6,
        'server_cert': settings.app.server_cert,
        'server_key': settings.app.server_key,
    })
    return utils.jsonify(response)

@app.app.route('/settings', methods=['PUT'])
@auth.session_auth
def settings_put():
    admin = flask.g.administrator

    if 'username' in flask.request.json and flask.request.json['username']:
        admin.username = utils.filter_str(
            flask.request.json['username']).lower()
    if 'password' in flask.request.json and flask.request.json['password']:
        admin.password = flask.request.json['password']
    if 'token' in flask.request.json and flask.request.json['token']:
        admin.generate_token()
    if 'secret' in flask.request.json and flask.request.json['secret']:
        admin.generate_secret()

    settings_commit = False
    if 'email_from' in flask.request.json:
        settings_commit = True
        email_from = flask.request.json['email_from']
        settings.app.email_from = email_from or None

    if 'email_server' in flask.request.json:
        settings_commit = True
        email_server = flask.request.json['email_server']
        settings.app.email_server = email_server or None

    if 'email_username' in flask.request.json:
        settings_commit = True
        email_username = flask.request.json['email_username']
        settings.app.email_username = email_username or None

    if 'email_password' in flask.request.json:
        settings_commit = True
        email_password = flask.request.json['email_password']
        settings.app.email_password = email_password or None

    if 'sso' in flask.request.json:
        settings_commit = True
        sso = flask.request.json['sso']
        settings.app.sso = sso or None

    if 'sso_match' in flask.request.json:
        sso_match = flask.request.json['sso_match']

        if isinstance(sso_match, list):
            settings_commit = True
            settings.app.sso_match = sso_match or None

    if 'sso_token' in flask.request.json:
        sso_token = flask.request.json['sso_token']
        settings_commit = True
        settings.app.sso_token = sso_token or None

    if 'sso_secret' in flask.request.json:
        sso_secret = flask.request.json['sso_secret']
        settings_commit = True
        settings.app.sso_secret = sso_secret or None

    if 'sso_host' in flask.request.json:
        sso_host = flask.request.json['sso_host']
        settings_commit = True
        settings.app.sso_host = sso_host or None

    if 'sso_admin' in flask.request.json:
        sso_admin = flask.request.json['sso_admin']
        settings_commit = True
        settings.app.sso_admin = sso_admin or None

    if 'sso_org' in flask.request.json:
        settings_commit = True
        sso_org = flask.request.json['sso_org']
        if sso_org:
            settings.app.sso_org = utils.ObjectId(sso_org)
        else:
            settings.app.sso_org = None

    if 'theme' in flask.request.json:
        settings_commit = True
        theme = 'dark' if flask.request.json['theme'] == 'dark' else 'light'

        if theme != settings.app.theme:
            if theme == 'dark':
                event.Event(type=THEME_DARK)
            else:
                event.Event(type=THEME_LIGHT)

        settings.app.theme = theme

    if 'public_address' in flask.request.json:
        public_address = flask.request.json['public_address']
        settings.local.host.public_address = public_address
        settings.local.host.commit('public_address')

    if 'public_address6' in flask.request.json:
        public_address6 = flask.request.json['public_address6']
        settings.local.host.public_address6 = public_address6
        settings.local.host.commit('public_address6')

    if 'routed_subnet6' in flask.request.json:
        routed_subnet6 = flask.request.json['routed_subnet6']
        if routed_subnet6:
            try:
                routed_subnet6 = ipaddress.IPv6Network(
                    flask.request.json['routed_subnet6'])
            except ipaddress.AddressValueError:
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

        if settings.local.host.routed_subnet6 != routed_subnet6:
            if server.get_online_ipv6_count():
                return utils.jsonify({
                    'error': IPV6_SUBNET_ONLINE,
                    'error_msg': IPV6_SUBNET_ONLINE_MSG,
                }, 400)
            settings.local.host.routed_subnet6 = routed_subnet6
            settings.local.host.commit('routed_subnet6')

    if 'server_cert' in flask.request.json:
        settings_commit = True
        server_cert = flask.request.json['server_cert']
        if server_cert:
            settings.app.server_cert = server_cert.strip()
        else:
            settings.app.server_cert = None

    if 'server_key' in flask.request.json:
        settings_commit = True
        server_key = flask.request.json['server_key']
        if server_key:
            settings.app.server_key = server_key.strip()
        else:
            settings.app.server_key = None

    if not settings.app.sso:
        settings.app.sso_match = None
        settings.app.sso_token = None
        settings.app.sso_secret = None
        settings.app.sso_host = None
        settings.app.sso_admin = None
        settings.app.sso_org = None

    if settings_commit:
        settings.commit()

    admin.commit(admin.changed)

    response = flask.g.administrator.dict()
    response.update({
        'theme': settings.app.theme,
        'email_from': settings.app.email_from,
        'email_server': settings.app.email_server,
        'email_username': settings.app.email_username,
        'email_password': bool(settings.app.email_password),
        'sso': settings.app.sso,
        'sso_match': settings.app.sso_match,
        'sso_token': settings.app.sso_token,
        'sso_secret': settings.app.sso_secret,
        'sso_host': settings.app.sso_host,
        'sso_admin': settings.app.sso_admin,
        'sso_org': settings.app.sso_org,
        'public_address': settings.local.host.public_addr,
    })
    return utils.jsonify(response)
