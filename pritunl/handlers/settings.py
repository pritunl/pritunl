from pritunl.constants import *
from pritunl import settings
from pritunl import utils
from pritunl import app
from pritunl import acme
from pritunl import auth
from pritunl import event
from pritunl import ipaddress
from pritunl import server
from pritunl import organization
from pritunl import logger

import flask

_changes_audit_text = {
    'username': 'Administrator username changed',
    'password': 'Administrator password changed',
    'smtp': 'SMTP settings changed',
    'pin_mode': 'User pin mode settings changed',
    'sso': 'Single sign-on settings changed',
}

def _dict():
    if settings.app.demo_mode:
        return {
            'acme_domain': settings.app.acme_domain,
            'theme': settings.app.theme,
            'auditing': settings.app.auditing,
            'monitoring': settings.app.monitoring,
            'datadog_api_key': settings.app.datadog_api_key,
            'email_from': settings.app.email_from,
            'email_server': 'demo',
            'email_username': 'demo',
            'email_password': True,
            'pin_mode': settings.user.pin_mode,
            'sso': settings.app.sso,
            'sso_match': settings.app.sso_match,
            'sso_token': 'demo',
            'sso_secret': 'demo',
            'sso_host': 'demo',
            'sso_org': settings.app.sso_org,
            'sso_saml_url': 'demo',
            'sso_saml_issuer_url': 'demo',
            'sso_saml_cert': 'demo',
            'sso_okta_token': 'demo',
            'sso_onelogin_key': 'demo',
            'public_address': settings.local.host.public_addr,
            'public_address6': settings.local.host.public_addr6,
            'routed_subnet6': settings.local.host.routed_subnet6,
            'server_port': settings.app.server_port,
            'server_cert': 'demo',
            'server_key': 'demo',
            'cloud_provider': settings.app.cloud_provider,
            'us_east_1_access_key': 'demo',
            'us_east_1_secret_key': 'demo',
            'us_west_1_access_key': 'demo',
            'us_west_1_secret_key': 'demo',
            'us_west_2_access_key': 'demo',
            'us_west_2_secret_key': 'demo',
            'eu_west_1_access_key': 'demo',
            'eu_west_1_secret_key': 'demo',
            'eu_central_1_access_key': 'demo',
            'eu_central_1_secret_key': 'demo',
            'ap_northeast_1_access_key': 'demo',
            'ap_northeast_1_secret_key': 'demo',
            'ap_northeast_2_access_key': 'demo',
            'ap_northeast_2_secret_key': 'demo',
            'ap_southeast_1_access_key': 'demo',
            'ap_southeast_1_secret_key': 'demo',
            'ap_southeast_2_access_key': 'demo',
            'ap_southeast_2_secret_key': 'demo',
            'sa_east_1_access_key': 'demo',
            'sa_east_1_secret_key': 'demo',
        }
    else:
        return {
            'acme_domain': settings.app.acme_domain,
            'theme': settings.app.theme,
            'auditing': settings.app.auditing,
            'monitoring': settings.app.monitoring,
            'datadog_api_key': settings.app.datadog_api_key,
            'email_from': settings.app.email_from,
            'email_server': settings.app.email_server,
            'email_username': settings.app.email_username,
            'email_password': bool(settings.app.email_password),
            'pin_mode': settings.user.pin_mode,
            'sso': settings.app.sso,
            'sso_match': settings.app.sso_match,
            'sso_token': settings.app.sso_token,
            'sso_secret': settings.app.sso_secret,
            'sso_host': settings.app.sso_host,
            'sso_org': settings.app.sso_org,
            'sso_saml_url': settings.app.sso_saml_url,
            'sso_saml_issuer_url': settings.app.sso_saml_issuer_url,
            'sso_saml_cert': settings.app.sso_saml_cert,
            'sso_okta_token': settings.app.sso_okta_token,
            'sso_onelogin_key': settings.app.sso_onelogin_key,
            'public_address': settings.local.host.public_addr,
            'public_address6': settings.local.host.public_addr6,
            'routed_subnet6': settings.local.host.routed_subnet6,
            'server_port': settings.app.server_port,
            'server_cert': settings.app.server_cert,
            'server_key': settings.app.server_key,
            'cloud_provider': settings.app.cloud_provider,
            'us_east_1_access_key': settings.app.us_east_1_access_key,
            'us_east_1_secret_key': settings.app.us_east_1_secret_key,
            'us_west_1_access_key': settings.app.us_west_1_access_key,
            'us_west_1_secret_key': settings.app.us_west_1_secret_key,
            'us_west_2_access_key': settings.app.us_west_2_access_key,
            'us_west_2_secret_key': settings.app.us_west_2_secret_key,
            'eu_west_1_access_key': settings.app.eu_west_1_access_key,
            'eu_west_1_secret_key': settings.app.eu_west_1_secret_key,
            'eu_central_1_access_key': settings.app.eu_central_1_access_key,
            'eu_central_1_secret_key': settings.app.eu_central_1_secret_key,
            'ap_northeast_1_access_key':
                settings.app.ap_northeast_1_access_key,
            'ap_northeast_1_secret_key':
                settings.app.ap_northeast_1_secret_key,
            'ap_northeast_2_access_key':
                settings.app.ap_northeast_2_access_key,
            'ap_northeast_2_secret_key':
                settings.app.ap_northeast_2_secret_key,
            'ap_southeast_1_access_key':
                settings.app.ap_southeast_1_access_key,
            'ap_southeast_1_secret_key':
                settings.app.ap_southeast_1_secret_key,
            'ap_southeast_2_access_key':
                settings.app.ap_southeast_2_access_key,
            'ap_southeast_2_secret_key':
                settings.app.ap_southeast_2_secret_key,
            'sa_east_1_access_key': settings.app.sa_east_1_access_key,
            'sa_east_1_secret_key': settings.app.sa_east_1_secret_key,
        }

@app.app.route('/settings', methods=['GET'])
@auth.session_auth
def settings_get():
    response = flask.g.administrator.dict()
    response.update(_dict())
    return utils.jsonify(response)

@app.app.route('/settings', methods=['PUT'])
@auth.session_auth
def settings_put():
    if settings.app.demo_mode:
        return utils.demo_blocked()

    org_event = False
    admin = flask.g.administrator
    changes = set()

    settings_commit = False
    update_server = False
    update_acme = False

    if 'username' in flask.request.json and flask.request.json['username']:
        username = utils.filter_str(
            flask.request.json['username']).lower()
        if username != admin.username:
            changes.add('username')
        admin.username = username

    if 'password' in flask.request.json and flask.request.json['password']:
        password = flask.request.json['password']
        changes.add('password')
        admin.password = password

    if 'token' in flask.request.json and flask.request.json['token']:
        admin.generate_token()
        changes.add('token')

    if 'secret' in flask.request.json and flask.request.json['secret']:
        admin.generate_secret()
        changes.add('token')

    if 'server_cert' in flask.request.json:
        settings_commit = True
        server_cert = flask.request.json['server_cert']
        if server_cert:
            server_cert = server_cert.strip()
        else:
            server_cert = None

        if server_cert != settings.app.server_cert:
            update_server = True

        settings.app.server_cert = server_cert

    if 'server_key' in flask.request.json:
        settings_commit = True
        server_key = flask.request.json['server_key']
        if server_key:
            server_key = server_key.strip()
        else:
            server_key = None

        if server_key != settings.app.server_key:
            update_server = True

        settings.app.server_key = server_key

    if 'server_port' in flask.request.json:
        settings_commit = True

        server_port = flask.request.json['server_port']
        if not server_port:
            server_port = 443

        try:
            server_port = int(server_port)
            if server_port < 1 or server_port > 65535:
                raise ValueError('Port invalid')
        except ValueError:
            return utils.jsonify({
                'error': PORT_INVALID,
                'error_msg': PORT_INVALID_MSG,
            }, 400)

        if settings.app.redirect_server and server_port == 80:
            return utils.jsonify({
                'error': PORT_RESERVED,
                'error_msg': PORT_RESERVED_MSG,
            }, 400)

        if server_port != settings.app.server_port:
            update_server = True

        settings.app.server_port = server_port

    if 'acme_domain' in flask.request.json:
        settings_commit = True

        acme_domain = utils.filter_str(
            flask.request.json['acme_domain'] or None)
        if acme_domain:
            acme_domain = acme_domain.replace('https://', '')
            acme_domain = acme_domain.replace('http://', '')
            acme_domain = acme_domain.replace('/', '')

        if acme_domain != settings.app.acme_domain:
            if not acme_domain:
                settings.app.acme_key = None
                settings.app.acme_timestamp = None
                settings.app.server_key = None
                settings.app.server_cert = None
                utils.create_server_cert()
                update_server = True
            else:
                update_acme = True
        settings.app.acme_domain = acme_domain

    if 'auditing' in flask.request.json:
        settings_commit = True
        auditing = flask.request.json['auditing'] or None

        if settings.app.auditing != auditing:
            if not flask.g.administrator.super_user:
                return utils.jsonify({
                    'error': REQUIRES_SUPER_USER,
                    'error_msg': REQUIRES_SUPER_USER_MSG,
                }, 400)
            org_event = True

        settings.app.auditing = auditing

    if 'monitoring' in flask.request.json:
        settings_commit = True
        monitoring = flask.request.json['monitoring'] or None
        settings.app.monitoring = monitoring

    if 'datadog_api_key' in flask.request.json:
        settings_commit = True
        datadog_api_key = flask.request.json['datadog_api_key'] or None
        settings.app.datadog_api_key = datadog_api_key

    if 'email_from' in flask.request.json:
        settings_commit = True
        email_from = flask.request.json['email_from'] or None
        if email_from != settings.app.email_from:
            changes.add('smtp')
        settings.app.email_from = email_from

    if 'email_server' in flask.request.json:
        settings_commit = True
        email_server = flask.request.json['email_server'] or None
        if email_server != settings.app.email_server:
            changes.add('smtp')
        settings.app.email_server = email_server

    if 'email_username' in flask.request.json:
        settings_commit = True
        email_username = flask.request.json['email_username'] or None
        if email_username != settings.app.email_username:
            changes.add('smtp')
        settings.app.email_username = email_username

    if 'email_password' in flask.request.json:
        settings_commit = True
        email_password = flask.request.json['email_password'] or None
        if email_password != settings.app.email_password:
            changes.add('smtp')
        settings.app.email_password = email_password

    if 'pin_mode' in flask.request.json:
        settings_commit = True
        pin_mode = flask.request.json['pin_mode'] or None
        if pin_mode != settings.user.pin_mode:
            changes.add('pin_mode')
        settings.user.pin_mode = pin_mode

    if 'sso' in flask.request.json:
        org_event = True
        settings_commit = True
        sso = flask.request.json['sso'] or None
        if sso != settings.app.sso:
            changes.add('sso')
        settings.app.sso = sso

    if 'sso_match' in flask.request.json:
        settings_commit = True
        sso_match = flask.request.json['sso_match'] or None

        if sso_match != settings.app.sso_match:
            changes.add('sso')

        if isinstance(sso_match, list):
            settings.app.sso_match = sso_match
        else:
            settings.app.sso_match = None

    if 'sso_token' in flask.request.json:
        settings_commit = True
        sso_token = flask.request.json['sso_token'] or None
        if sso_token != settings.app.sso_token:
            changes.add('sso')
        settings.app.sso_token = sso_token

    if 'sso_secret' in flask.request.json:
        settings_commit = True
        sso_secret = flask.request.json['sso_secret'] or None
        if sso_secret != settings.app.sso_secret:
            changes.add('sso')
        settings.app.sso_secret = sso_secret

    if 'sso_host' in flask.request.json:
        settings_commit = True
        sso_host = flask.request.json['sso_host'] or None
        if sso_host != settings.app.sso_host:
            changes.add('sso')
        settings.app.sso_host = sso_host

    if 'sso_org' in flask.request.json:
        settings_commit = True
        sso_org = flask.request.json['sso_org']

        if sso_org:
            sso_org = utils.ObjectId(sso_org)
        else:
            sso_org = None

        if sso_org != settings.app.sso_org:
            changes.add('sso')

        settings.app.sso_org = sso_org

    if 'sso_saml_url' in flask.request.json:
        settings_commit = True
        sso_saml_url = flask.request.json['sso_saml_url'] or None
        if sso_saml_url != settings.app.sso_saml_url:
            changes.add('sso')
        settings.app.sso_saml_url = sso_saml_url

    if 'sso_saml_issuer_url' in flask.request.json:
        settings_commit = True
        sso_saml_issuer_url = flask.request.json['sso_saml_issuer_url'] or None
        if sso_saml_issuer_url != settings.app.sso_saml_issuer_url:
            changes.add('sso')
        settings.app.sso_saml_issuer_url = sso_saml_issuer_url

    if 'sso_saml_cert' in flask.request.json:
        settings_commit = True
        sso_saml_cert = flask.request.json['sso_saml_cert'] or None
        if sso_saml_cert != settings.app.sso_saml_cert:
            changes.add('sso')
        settings.app.sso_saml_cert = sso_saml_cert

    if 'sso_okta_token' in flask.request.json:
        settings_commit = True
        sso_okta_token = flask.request.json['sso_okta_token'] or None
        if sso_okta_token != settings.app.sso_okta_token:
            changes.add('sso')
        settings.app.sso_okta_token = sso_okta_token

    if 'sso_onelogin_key' in flask.request.json:
        settings_commit = True
        sso_onelogin_key = flask.request.json['sso_onelogin_key'] or None
        if sso_onelogin_key != settings.app.sso_onelogin_key:
            changes.add('sso')
        settings.app.sso_onelogin_key = sso_onelogin_key

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

        if settings.local.host.routed_subnet6 != routed_subnet6:
            if server.get_online_ipv6_count():
                return utils.jsonify({
                    'error': IPV6_SUBNET_ONLINE,
                    'error_msg': IPV6_SUBNET_ONLINE_MSG,
                }, 400)
            settings.local.host.routed_subnet6 = routed_subnet6
            settings.local.host.commit('routed_subnet6')

    if 'cloud_provider' in flask.request.json:
        settings_commit = True
        cloud_provider = flask.request.json['cloud_provider']
        if cloud_provider:
            settings.app.cloud_provider = cloud_provider
        else:
            settings.app.cloud_provider = None

    for aws_key in (
                'us_east_1_access_key',
                'us_east_1_secret_key',
                'us_west_1_access_key',
                'us_west_1_secret_key',
                'us_west_2_access_key',
                'us_west_2_secret_key',
                'eu_west_1_access_key',
                'eu_west_1_secret_key',
                'eu_central_1_access_key',
                'eu_central_1_secret_key',
                'ap_northeast_1_access_key',
                'ap_northeast_1_secret_key',
                'ap_northeast_2_access_key',
                'ap_northeast_2_secret_key',
                'ap_southeast_1_access_key',
                'ap_southeast_1_secret_key',
                'ap_southeast_2_access_key',
                'ap_southeast_2_secret_key',
                'sa_east_1_access_key',
                'sa_east_1_secret_key',
            ):
        if aws_key in flask.request.json:
            settings_commit = True
            aws_value = flask.request.json[aws_key]

            if aws_value:
                setattr(settings.app, aws_key, utils.filter_str(aws_value))
            else:
                setattr(settings.app, aws_key, None)

    if not settings.app.sso:
        settings.app.sso_match = None
        settings.app.sso_token = None
        settings.app.sso_secret = None
        settings.app.sso_host = None
        settings.app.sso_org = None
        settings.app.sso_saml_url = None
        settings.app.sso_saml_issuer_url = None
        settings.app.sso_saml_cert = None
        settings.app.sso_okta_token = None
        settings.app.sso_onelogin_key = None

    for change in changes:
        flask.g.administrator.audit_event(
            'admin_settings',
            _changes_audit_text[change],
            remote_addr=utils.get_remote_addr(),
        )

    if settings_commit:
        settings.commit()

    admin.commit(admin.changed)

    if org_event:
        for org in organization.iter_orgs(fields=('_id')):
            event.Event(type=USERS_UPDATED, resource_id=org.id)

    event.Event(type=SETTINGS_UPDATED)

    if update_server:
        app.update_server(0.5)

    if update_acme:
        try:
            acme.update_acme_cert()
            app.update_server(0.5)
        except:
            logger.exception('Failed to get LetsEncrypt cert', 'handler',
                acme_domain=settings.app.acme_domain,
            )
            settings.app.acme_domain = None
            settings.app.acme_key = None
            settings.commit()
            return utils.jsonify({
                'error': ACME_ERROR,
                'error_msg': ACME_ERROR_MSG,
            }, 400)

    response = flask.g.administrator.dict()
    response.update(_dict())
    return utils.jsonify(response)
