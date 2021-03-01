from pritunl.constants import *
from pritunl import settings
from pritunl import utils
from pritunl import app
from pritunl import acme
from pritunl import journal
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
    'pin_mode': 'User pin mode setting changed',
    'restrict_import': 'Restrict import setting changed',
    'sso': 'Single sign-on settings changed',
}

def _dict():
    if settings.app.demo_mode:
        return {
            'acme_domain': settings.app.acme_domain,
            'theme': settings.app.theme,
            'auditing': settings.app.auditing,
            'monitoring': settings.app.monitoring,
            'influxdb_url': 'demo',
            'influxdb_token': 'demo',
            'influxdb_org': 'demo',
            'influxdb_bucket': 'demo',
            'email_from': settings.app.email_from,
            'email_server': 'demo',
            'email_username': 'demo',
            'email_password': 'demo',
            'pin_mode': settings.user.pin_mode,
            'sso': settings.app.sso,
            'sso_match': settings.app.sso_match,
            'sso_azure_directory_id': 'demo',
            'sso_azure_app_id': 'demo',
            'sso_azure_app_secret': 'demo',
            'sso_authzero_domain': 'demo',
            'sso_authzero_app_id': 'demo',
            'sso_authzero_app_secret': 'demo',
            'sso_google_key': 'demo',
            'sso_google_email': 'demo',
            'sso_duo_token': 'demo',
            'sso_duo_secret': 'demo',
            'sso_duo_host': 'demo',
            'sso_duo_mode': settings.app.sso_duo_mode,
            'sso_yubico_client': 'demo',
            'sso_yubico_secret': 'demo',
            'sso_org': settings.app.sso_org,
            'sso_saml_url': 'demo',
            'sso_saml_issuer_url': 'demo',
            'sso_saml_cert': 'demo',
            'sso_okta_app_id': settings.app.sso_okta_app_id,
            'sso_okta_token': 'demo',
            'sso_okta_mode': utils.get_okta_mode(),
            'sso_onelogin_app_id': settings.app.sso_onelogin_app_id,
            'sso_onelogin_id': 'demo',
            'sso_onelogin_secret': 'demo',
            'sso_onelogin_mode': utils.get_onelogin_mode(),
            'sso_radius_secret': 'demo',
            'sso_radius_host': 'demo',
            'sso_cache': settings.app.sso_cache,
            'sso_client_cache': settings.app.sso_client_cache,
            'restrict_import': settings.user.restrict_import,
            'client_reconnect': settings.user.reconnect,
            'public_address': settings.local.host.public_addr,
            'public_address6': settings.local.host.public_addr6,
            'routed_subnet6': settings.local.host.routed_subnet6,
            'routed_subnet6_wg': settings.local.host.routed_subnet6_wg,
            'reverse_proxy': settings.app.reverse_proxy,
            'server_port': settings.app.server_port,
            'server_cert': 'demo',
            'server_key': 'demo',
            'cloud_provider': settings.app.cloud_provider,
            'route53_region': settings.app.route53_region,
            'route53_zone': settings.app.route53_zone,
            'oracle_user_ocid': settings.app.oracle_user_ocid,
            'oracle_public_key': 'demo',
            'us_east_1_access_key': 'demo',
            'us_east_1_secret_key': 'demo',
            'us_east_2_access_key': 'demo',
            'us_east_2_secret_key': 'demo',
            'us_west_1_access_key': 'demo',
            'us_west_1_secret_key': 'demo',
            'us_west_2_access_key': 'demo',
            'us_west_2_secret_key': 'demo',
            'us_gov_east_1_access_key': 'demo',
            'us_gov_east_1_secret_key': 'demo',
            'us_gov_west_1_access_key': 'demo',
            'us_gov_west_1_secret_key': 'demo',
            'eu_north_1_access_key': 'demo',
            'eu_north_1_secret_key': 'demo',
            'eu_west_1_access_key': 'demo',
            'eu_west_1_secret_key': 'demo',
            'eu_west_2_access_key': 'demo',
            'eu_west_2_secret_key': 'demo',
            'eu_west_3_access_key': 'demo',
            'eu_west_3_secret_key': 'demo',
            'eu_central_1_access_key': 'demo',
            'eu_central_1_secret_key': 'demo',
            'ca_central_1_access_key': 'demo',
            'ca_central_1_secret_key': 'demo',
            'cn_north_1_access_key': 'demo',
            'cn_north_1_secret_key': 'demo',
            'cn_northwest_1_access_key': 'demo',
            'cn_northwest_1_secret_key': 'demo',
            'ap_northeast_1_access_key': 'demo',
            'ap_northeast_1_secret_key': 'demo',
            'ap_northeast_2_access_key': 'demo',
            'ap_northeast_2_secret_key': 'demo',
            'ap_southeast_1_access_key': 'demo',
            'ap_southeast_1_secret_key': 'demo',
            'ap_southeast_2_access_key': 'demo',
            'ap_southeast_2_secret_key': 'demo',
            'ap_east_1_access_key': 'demo',
            'ap_east_1_secret_key': 'demo',
            'ap_south_1_access_key': 'demo',
            'ap_south_1_secret_key': 'demo',
            'sa_east_1_access_key': 'demo',
            'sa_east_1_secret_key': 'demo',
        }
    else:
        return {
            'acme_domain': settings.app.acme_domain,
            'theme': settings.app.theme,
            'auditing': settings.app.auditing,
            'monitoring': settings.app.monitoring,
            'influxdb_url': settings.app.influxdb_url,
            'influxdb_token': settings.app.influxdb_token,
            'influxdb_org': settings.app.influxdb_org,
            'influxdb_bucket': settings.app.influxdb_bucket,
            'email_from': settings.app.email_from,
            'email_server': settings.app.email_server,
            'email_username': settings.app.email_username,
            'email_password': settings.app.email_password,
            'pin_mode': settings.user.pin_mode,
            'sso': settings.app.sso,
            'sso_match': settings.app.sso_match,
            'sso_azure_directory_id': settings.app.sso_azure_directory_id,
            'sso_azure_app_id': settings.app.sso_azure_app_id,
            'sso_azure_app_secret': settings.app.sso_azure_app_secret,
            'sso_authzero_domain': settings.app.sso_authzero_domain,
            'sso_authzero_app_id': settings.app.sso_authzero_app_id,
            'sso_authzero_app_secret': settings.app.sso_authzero_app_secret,
            'sso_google_key': settings.app.sso_google_key,
            'sso_google_email': settings.app.sso_google_email,
            'sso_duo_token': settings.app.sso_duo_token,
            'sso_duo_secret': settings.app.sso_duo_secret,
            'sso_duo_host': settings.app.sso_duo_host,
            'sso_duo_mode': settings.app.sso_duo_mode,
            'sso_yubico_client': settings.app.sso_yubico_client,
            'sso_yubico_secret': settings.app.sso_yubico_secret,
            'sso_org': settings.app.sso_org,
            'sso_saml_url': settings.app.sso_saml_url,
            'sso_saml_issuer_url': settings.app.sso_saml_issuer_url,
            'sso_saml_cert': settings.app.sso_saml_cert,
            'sso_okta_app_id': settings.app.sso_okta_app_id,
            'sso_okta_token': settings.app.sso_okta_token,
            'sso_okta_mode': utils.get_okta_mode(),
            'sso_onelogin_app_id': settings.app.sso_onelogin_app_id,
            'sso_onelogin_id': settings.app.sso_onelogin_id,
            'sso_onelogin_secret': settings.app.sso_onelogin_secret,
            'sso_onelogin_mode': utils.get_onelogin_mode(),
            'sso_radius_secret': settings.app.sso_radius_secret,
            'sso_radius_host': settings.app.sso_radius_host,
            'sso_cache': settings.app.sso_cache,
            'sso_client_cache': settings.app.sso_client_cache,
            'restrict_import': settings.user.restrict_import,
            'client_reconnect': settings.user.reconnect,
            'public_address': settings.local.host.public_addr,
            'public_address6': settings.local.host.public_addr6,
            'routed_subnet6': settings.local.host.routed_subnet6,
            'routed_subnet6_wg': settings.local.host.routed_subnet6_wg,
            'reverse_proxy': settings.app.reverse_proxy,
            'server_port': settings.app.server_port,
            'server_cert': settings.app.server_cert,
            'server_key': settings.app.server_key,
            'cloud_provider': settings.app.cloud_provider,
            'route53_region': settings.app.route53_region,
            'route53_zone': settings.app.route53_zone,
            'oracle_user_ocid': settings.app.oracle_user_ocid,
            'oracle_public_key': settings.app.oracle_public_key,
            'us_east_1_access_key': settings.app.us_east_1_access_key,
            'us_east_1_secret_key': settings.app.us_east_1_secret_key,
            'us_east_2_access_key': settings.app.us_east_2_access_key,
            'us_east_2_secret_key': settings.app.us_east_2_secret_key,
            'us_west_1_access_key': settings.app.us_west_1_access_key,
            'us_west_1_secret_key': settings.app.us_west_1_secret_key,
            'us_west_2_access_key': settings.app.us_west_2_access_key,
            'us_west_2_secret_key': settings.app.us_west_2_secret_key,
            'us_gov_east_1_access_key':
                settings.app.us_gov_east_1_access_key,
            'us_gov_east_1_secret_key':
                settings.app.us_gov_east_1_secret_key,
            'us_gov_west_1_access_key':
                settings.app.us_gov_west_1_access_key,
            'us_gov_west_1_secret_key':
                settings.app.us_gov_west_1_secret_key,
            'eu_north_1_access_key': settings.app.eu_north_1_access_key,
            'eu_north_1_secret_key': settings.app.eu_north_1_secret_key,
            'eu_west_1_access_key': settings.app.eu_west_1_access_key,
            'eu_west_1_secret_key': settings.app.eu_west_1_secret_key,
            'eu_west_2_access_key': settings.app.eu_west_2_access_key,
            'eu_west_2_secret_key': settings.app.eu_west_2_secret_key,
            'eu_west_3_access_key': settings.app.eu_west_3_access_key,
            'eu_west_3_secret_key': settings.app.eu_west_3_secret_key,
            'eu_central_1_access_key': settings.app.eu_central_1_access_key,
            'eu_central_1_secret_key': settings.app.eu_central_1_secret_key,
            'ca_central_1_access_key': settings.app.ca_central_1_access_key,
            'ca_central_1_secret_key': settings.app.ca_central_1_secret_key,
            'cn_north_1_access_key': settings.app.cn_north_1_access_key,
            'cn_north_1_secret_key': settings.app.cn_north_1_secret_key,
            'cn_northwest_1_access_key':
                settings.app.cn_northwest_1_access_key,
            'cn_northwest_1_secret_key':
                settings.app.cn_northwest_1_secret_key,
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
            'ap_east_1_access_key':
                settings.app.ap_east_1_access_key,
            'ap_east_1_secret_key':
                settings.app.ap_east_1_secret_key,
            'ap_south_1_access_key':
                settings.app.ap_south_1_access_key,
            'ap_south_1_secret_key':
                settings.app.ap_south_1_secret_key,
            'sa_east_1_access_key': settings.app.sa_east_1_access_key,
            'sa_east_1_secret_key': settings.app.sa_east_1_secret_key,
        }

@app.app.route('/settings', methods=['GET'])
@auth.session_auth
def settings_get():
    if settings.app.demo_mode:
        resp = utils.demo_get_cache()
        if resp:
            return utils.jsonify(resp)

    response = flask.g.administrator.dict()
    response.update(_dict())

    if settings.app.demo_mode:
        utils.demo_set_cache(response)
    return utils.jsonify(response)

@app.app.route('/settings', methods=['PUT'])
@auth.session_auth
def settings_put():
    if settings.app.demo_mode:
        return utils.demo_blocked()

    org_event = False
    admin_event = False
    admin = flask.g.administrator
    changes = set()

    settings_commit = False
    update_server = False
    update_acme = False
    update_cert = False

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
                update_server = True
                update_cert = True
            else:
                update_acme = True
        settings.app.acme_domain = acme_domain

    if 'auditing' in flask.request.json:
        settings_commit = True
        auditing = flask.request.json['auditing'] or None

        if settings.app.auditing == ALL and auditing != ALL:
            return utils.jsonify({
                'error': CANNOT_DISABLE_AUTIDING,
                'error_msg': CANNOT_DISABLE_AUTIDING_MSG,
            }, 400)

        if settings.app.auditing != auditing:
            if not flask.g.administrator.super_user:
                return utils.jsonify({
                    'error': REQUIRES_SUPER_USER,
                    'error_msg': REQUIRES_SUPER_USER_MSG,
                }, 400)
            admin_event = True
            org_event = True

        settings.app.auditing = auditing

    if 'monitoring' in flask.request.json:
        settings_commit = True
        monitoring = flask.request.json['monitoring'] or None
        settings.app.monitoring = monitoring

    if 'influxdb_url' in flask.request.json:
        settings_commit = True
        influxdb_url = flask.request.json['influxdb_url'] or None
        settings.app.influxdb_url = influxdb_url

    if 'influxdb_token' in flask.request.json:
        settings_commit = True
        influxdb_token = flask.request.json['influxdb_token'] or None
        settings.app.influxdb_token = influxdb_token

    if 'influxdb_org' in flask.request.json:
        settings_commit = True
        influxdb_org = flask.request.json['influxdb_org'] or None
        settings.app.influxdb_org = influxdb_org

    if 'influxdb_bucket' in flask.request.json:
        settings_commit = True
        influxdb_bucket = flask.request.json['influxdb_bucket'] or None
        settings.app.influxdb_bucket = influxdb_bucket

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

    if 'sso_azure_directory_id' in flask.request.json:
        settings_commit = True
        sso_azure_directory_id = flask.request.json[
            'sso_azure_directory_id'] or None
        if sso_azure_directory_id != settings.app.sso_azure_directory_id:
            changes.add('sso')
        settings.app.sso_azure_directory_id = sso_azure_directory_id

    if 'sso_azure_app_id' in flask.request.json:
        settings_commit = True
        sso_azure_app_id = flask.request.json['sso_azure_app_id'] or None
        if sso_azure_app_id != settings.app.sso_azure_app_id:
            changes.add('sso')
        settings.app.sso_azure_app_id = sso_azure_app_id

    if 'sso_azure_app_secret' in flask.request.json:
        settings_commit = True
        sso_azure_app_secret = flask.request.json[
            'sso_azure_app_secret'] or None
        if sso_azure_app_secret != settings.app.sso_azure_app_secret:
            changes.add('sso')
        settings.app.sso_azure_app_secret = sso_azure_app_secret

    if 'sso_authzero_domain' in flask.request.json:
        settings_commit = True
        sso_authzero_domain = flask.request.json[
            'sso_authzero_domain'] or None
        if sso_authzero_domain != settings.app.sso_authzero_domain:
            changes.add('sso')
        settings.app.sso_authzero_domain = sso_authzero_domain

    if 'sso_authzero_app_id' in flask.request.json:
        settings_commit = True
        sso_authzero_app_id = flask.request.json[
            'sso_authzero_app_id'] or None
        if sso_authzero_app_id != settings.app.sso_authzero_app_id:
            changes.add('sso')
        settings.app.sso_authzero_app_id = sso_authzero_app_id

    if 'sso_authzero_app_secret' in flask.request.json:
        settings_commit = True
        sso_authzero_app_secret = flask.request.json[
            'sso_authzero_app_secret'] or None
        if sso_authzero_app_secret != settings.app.sso_authzero_app_secret:
            changes.add('sso')
        settings.app.sso_authzero_app_secret = sso_authzero_app_secret

    if 'sso_google_key' in flask.request.json:
        settings_commit = True
        sso_google_key = flask.request.json['sso_google_key'] or None
        if sso_google_key != settings.app.sso_google_key:
            changes.add('sso')
        settings.app.sso_google_key = sso_google_key

    if 'sso_google_email' in flask.request.json:
        settings_commit = True
        sso_google_email = flask.request.json['sso_google_email'] or None
        if sso_google_email != settings.app.sso_google_email:
            changes.add('sso')
        settings.app.sso_google_email = sso_google_email

    if 'sso_duo_token' in flask.request.json:
        settings_commit = True
        sso_duo_token = flask.request.json['sso_duo_token'] or None
        if sso_duo_token != settings.app.sso_duo_token:
            changes.add('sso')
        settings.app.sso_duo_token = sso_duo_token

    if 'sso_duo_secret' in flask.request.json:
        settings_commit = True
        sso_duo_secret = flask.request.json['sso_duo_secret'] or None
        if sso_duo_secret != settings.app.sso_duo_secret:
            changes.add('sso')
        settings.app.sso_duo_secret = sso_duo_secret

    if 'sso_duo_host' in flask.request.json:
        settings_commit = True
        sso_duo_host = flask.request.json['sso_duo_host'] or None
        if sso_duo_host != settings.app.sso_duo_host:
            changes.add('sso')
        settings.app.sso_duo_host = sso_duo_host

    if 'sso_duo_mode' in flask.request.json:
        settings_commit = True
        sso_duo_mode = flask.request.json['sso_duo_mode'] or None
        if sso_duo_mode != settings.app.sso_duo_mode:
            changes.add('sso')
        settings.app.sso_duo_mode = sso_duo_mode

    if 'sso_radius_secret' in flask.request.json:
        settings_commit = True
        sso_radius_secret = flask.request.json['sso_radius_secret'] or None
        if sso_radius_secret != settings.app.sso_radius_secret:
            changes.add('sso')
        settings.app.sso_radius_secret = sso_radius_secret

    if 'sso_radius_host' in flask.request.json:
        settings_commit = True
        sso_radius_host = flask.request.json['sso_radius_host'] or None
        if sso_radius_host != settings.app.sso_radius_host:
            changes.add('sso')
        settings.app.sso_radius_host = sso_radius_host

    if 'sso_org' in flask.request.json:
        settings_commit = True
        sso_org = flask.request.json['sso_org'] or None

        if sso_org:
            sso_org = utils.ObjectId(sso_org)
        else:
            sso_org = None

        if sso_org != settings.app.sso_org:
            changes.add('sso')

        if settings.app.sso and not sso_org:
            return utils.jsonify({
                'error': SSO_ORG_NULL,
                'error_msg': SSO_ORG_NULL_MSG,
            }, 400)

        settings.app.sso_org = sso_org

    if 'sso_saml_url' in flask.request.json:
        settings_commit = True
        sso_saml_url = flask.request.json['sso_saml_url'] or None
        if sso_saml_url != settings.app.sso_saml_url:
            changes.add('sso')
        settings.app.sso_saml_url = sso_saml_url

    if 'sso_saml_issuer_url' in flask.request.json:
        settings_commit = True
        sso_saml_issuer_url = flask.request.json['sso_saml_issuer_url'] or \
            None
        if sso_saml_issuer_url != settings.app.sso_saml_issuer_url:
            changes.add('sso')
        settings.app.sso_saml_issuer_url = sso_saml_issuer_url

    if 'sso_saml_cert' in flask.request.json:
        settings_commit = True
        sso_saml_cert = flask.request.json['sso_saml_cert'] or None
        if sso_saml_cert != settings.app.sso_saml_cert:
            changes.add('sso')
        settings.app.sso_saml_cert = sso_saml_cert

    if 'sso_okta_app_id' in flask.request.json:
        settings_commit = True
        sso_okta_app_id = flask.request.json['sso_okta_app_id'] or None
        if sso_okta_app_id != settings.app.sso_okta_app_id:
            changes.add('sso')
        settings.app.sso_okta_app_id = sso_okta_app_id

    if 'sso_okta_token' in flask.request.json:
        settings_commit = True
        sso_okta_token = flask.request.json['sso_okta_token'] or None
        if sso_okta_token != settings.app.sso_okta_token:
            changes.add('sso')
        settings.app.sso_okta_token = sso_okta_token

    if 'sso_okta_mode' in flask.request.json:
        sso_mode = settings.app.sso
        if sso_mode and sso_mode == SAML_OKTA_AUTH:
            settings_commit = True
            sso_okta_mode = flask.request.json['sso_okta_mode']
            settings.app.sso_okta_mode = sso_okta_mode

    if 'sso_onelogin_app_id' in flask.request.json:
        settings_commit = True
        sso_onelogin_app_id = flask.request.json['sso_onelogin_app_id'] or \
            None
        if sso_onelogin_app_id != settings.app.sso_onelogin_app_id:
            changes.add('sso')
        settings.app.sso_onelogin_app_id = sso_onelogin_app_id

    if 'sso_onelogin_id' in flask.request.json:
        settings_commit = True
        sso_onelogin_id = flask.request.json['sso_onelogin_id'] or None
        if sso_onelogin_id != settings.app.sso_onelogin_id:
            changes.add('sso')
        settings.app.sso_onelogin_id = sso_onelogin_id

    if 'sso_onelogin_secret' in flask.request.json:
        settings_commit = True
        sso_onelogin_secret = \
            flask.request.json['sso_onelogin_secret'] or None
        if sso_onelogin_secret != settings.app.sso_onelogin_secret:
            changes.add('sso')
        settings.app.sso_onelogin_secret = sso_onelogin_secret

    if 'sso_onelogin_mode' in flask.request.json:
        sso_mode = settings.app.sso
        if sso_mode and sso_mode == SAML_ONELOGIN_AUTH:
            settings_commit = True
            sso_onelogin_mode = flask.request.json['sso_onelogin_mode']
            settings.app.sso_onelogin_mode = sso_onelogin_mode

    if 'sso_cache' in flask.request.json:
        settings_commit = True
        sso_cache = True if \
            flask.request.json['sso_cache'] else False
        if sso_cache != settings.app.sso_cache:
            changes.add('sso')
        settings.app.sso_cache = sso_cache

    if 'sso_client_cache' in flask.request.json:
        settings_commit = True
        sso_client_cache = True if \
            flask.request.json['sso_client_cache'] else False
        if sso_client_cache != settings.app.sso_client_cache:
            changes.add('sso')
        settings.app.sso_client_cache = sso_client_cache

    if 'restrict_import' in flask.request.json:
        settings_commit = True
        restrict_import = True if \
            flask.request.json['restrict_import'] else False
        if restrict_import != settings.user.restrict_import:
            changes.add('restrict_import')
        settings.user.restrict_import = restrict_import

    if 'client_reconnect' in flask.request.json:
        settings_commit = True
        client_reconnect = True if \
            flask.request.json['client_reconnect'] else False
        settings.user.reconnect = client_reconnect

    if 'sso_yubico_client' in flask.request.json:
        settings_commit = True
        sso_yubico_client = \
            flask.request.json['sso_yubico_client'] or None
        if sso_yubico_client != settings.app.sso_yubico_client:
            changes.add('sso')
        settings.app.sso_yubico_client = sso_yubico_client

    if 'sso_yubico_secret' in flask.request.json:
        settings_commit = True
        sso_yubico_secret = \
            flask.request.json['sso_yubico_secret'] or None
        if sso_yubico_secret != settings.app.sso_yubico_secret:
            changes.add('sso')
        settings.app.sso_yubico_secret = sso_yubico_secret

    if flask.request.json.get('theme'):
        settings_commit = True
        theme = 'light' if flask.request.json['theme'] == 'light' else 'dark'

        if theme != settings.app.theme:
            if theme == 'dark':
                event.Event(type=THEME_DARK)
            else:
                event.Event(type=THEME_LIGHT)

        settings.app.theme = theme

    if 'public_address' in flask.request.json:
        public_address = flask.request.json['public_address'] or None

        if public_address != settings.local.host.public_addr:
            settings.local.host.public_address = public_address
            settings.local.host.commit('public_address')

    if 'public_address6' in flask.request.json:
        public_address6 = flask.request.json['public_address6'] or None

        if public_address6 != settings.local.host.public_addr6:
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

    if 'routed_subnet6_wg' in flask.request.json:
        routed_subnet6_wg = flask.request.json['routed_subnet6_wg']
        if routed_subnet6_wg:
            try:
                routed_subnet6_wg = ipaddress.IPv6Network(
                    flask.request.json['routed_subnet6_wg'])
            except (ipaddress.AddressValueError, ValueError):
                return utils.jsonify({
                    'error': IPV6_SUBNET_WG_INVALID,
                    'error_msg': IPV6_SUBNET_WG_INVALID_MSG,
                }, 400)

            if routed_subnet6_wg.prefixlen > 64:
                return utils.jsonify({
                    'error': IPV6_SUBNET_WG_SIZE_INVALID,
                    'error_msg': IPV6_SUBNET_WG_SIZE_INVALID_MSG,
                }, 400)

            routed_subnet6_wg = str(routed_subnet6_wg)
        else:
            routed_subnet6_wg = None

        if settings.local.host.routed_subnet6_wg != routed_subnet6_wg:
            if server.get_online_ipv6_count():
                return utils.jsonify({
                    'error': IPV6_SUBNET_WG_ONLINE,
                    'error_msg': IPV6_SUBNET_WG_ONLINE_MSG,
                }, 400)
            settings.local.host.routed_subnet6_wg = routed_subnet6_wg
            settings.local.host.commit('routed_subnet6_wg')

    if 'reverse_proxy' in flask.request.json:
        settings_commit = True
        reverse_proxy = flask.request.json['reverse_proxy']
        settings.app.reverse_proxy = True if reverse_proxy else False

    if 'cloud_provider' in flask.request.json:
        settings_commit = True
        cloud_provider = flask.request.json['cloud_provider'] or None
        settings.app.cloud_provider = cloud_provider

    if 'route53_region' in flask.request.json:
        settings_commit = True
        settings.app.route53_region = utils.filter_str(
            flask.request.json['route53_region']) or None

    if 'route53_zone' in flask.request.json:
        settings_commit = True
        settings.app.route53_zone = utils.filter_str(
            flask.request.json['route53_zone']) or None

    if settings.app.cloud_provider == 'oracle':
        if 'oracle_user_ocid' in flask.request.json:
            settings_commit = True
            settings.app.oracle_user_ocid = utils.filter_str(
                flask.request.json['oracle_user_ocid']) or None
    elif settings.app.oracle_user_ocid:
        settings_commit = True
        settings.app.oracle_user_ocid = None

    if 'oracle_public_key' in flask.request.json:
        if flask.request.json['oracle_public_key'] == 'reset':
            settings_commit = True
            private_key, public_key = utils.generate_rsa_key()
            settings.app.oracle_private_key = private_key
            settings.app.oracle_public_key = public_key

    for aws_key in (
                'us_east_1_access_key',
                'us_east_1_secret_key',
                'us_east_2_access_key',
                'us_east_2_secret_key',
                'us_west_1_access_key',
                'us_west_1_secret_key',
                'us_west_2_access_key',
                'us_west_2_secret_key',
                'us_gov_east_1_access_key',
                'us_gov_east_1_secret_key',
                'us_gov_west_1_access_key',
                'us_gov_west_1_secret_key',
                'eu_north_1_access_key',
                'eu_north_1_secret_key',
                'eu_west_1_access_key',
                'eu_west_1_secret_key',
                'eu_west_2_access_key',
                'eu_west_2_secret_key',
                'eu_west_3_access_key',
                'eu_west_3_secret_key',
                'eu_central_1_access_key',
                'eu_central_1_secret_key',
                'ca_central_1_access_key',
                'ca_central_1_secret_key',
                'cn_north_1_access_key',
                'cn_north_1_secret_key',
                'cn_northwest_1_access_key',
                'cn_northwest_1_secret_key',
                'ap_northeast_1_access_key',
                'ap_northeast_1_secret_key',
                'ap_northeast_2_access_key',
                'ap_northeast_2_secret_key',
                'ap_southeast_1_access_key',
                'ap_southeast_1_secret_key',
                'ap_southeast_2_access_key',
                'ap_southeast_2_secret_key',
                'ap_east_1_access_key',
                'ap_east_1_secret_key',
                'ap_south_1_access_key',
                'ap_south_1_secret_key',
                'sa_east_1_access_key',
                'sa_east_1_secret_key',
            ):
        if settings.app.cloud_provider != 'aws':
            settings_commit = True
            setattr(settings.app, aws_key, None)
        elif aws_key in flask.request.json:
            settings_commit = True
            aws_value = flask.request.json[aws_key]

            if aws_value:
                setattr(settings.app, aws_key, utils.filter_str(aws_value))
            else:
                setattr(settings.app, aws_key, None)

    if not settings.app.sso:
        settings.app.sso_match = None
        settings.app.sso_azure_directory_id = None
        settings.app.sso_azure_app_id = None
        settings.app.sso_azure_app_secret = None
        settings.app.sso_authzero_directory_id = None
        settings.app.sso_authzero_app_id = None
        settings.app.sso_authzero_app_secret = None
        settings.app.sso_google_key = None
        settings.app.sso_google_email = None
        settings.app.sso_duo_token = None
        settings.app.sso_duo_secret = None
        settings.app.sso_duo_host = None
        settings.app.sso_org = None
        settings.app.sso_saml_url = None
        settings.app.sso_saml_issuer_url = None
        settings.app.sso_saml_cert = None
        settings.app.sso_okta_app_id = None
        settings.app.sso_okta_token = None
        settings.app.sso_onelogin_key = None
        settings.app.sso_onelogin_app_id = None
        settings.app.sso_onelogin_id = None
        settings.app.sso_onelogin_secret = None
        settings.app.sso_radius_secret = None
        settings.app.sso_radius_host = None
    else:
        if RADIUS_AUTH in settings.app.sso and \
                settings.app.sso_duo_mode == 'passcode':
            return utils.jsonify({
                'error': RADIUS_DUO_PASSCODE,
                'error_msg': RADIUS_DUO_PASSCODE_MSG,
            }, 400)

        if settings.app.sso == DUO_AUTH and \
                settings.app.sso_duo_mode == 'passcode':
            return utils.jsonify({
                'error': DUO_PASSCODE,
                'error_msg': DUO_PASSCODE_MSG,
            }, 400)

    for change in changes:
        remote_addr = utils.get_remote_addr()
        flask.g.administrator.audit_event(
            'admin_settings',
            _changes_audit_text[change],
            remote_addr=remote_addr,
        )
        journal.entry(
            journal.SETTINGS_UPDATE,
            remote_address=remote_addr,
            event_long='Settings updated',
            changed=_changes_audit_text[change],
        )

    if settings_commit:
        settings.commit()

    admin.commit(admin.changed)

    if admin_event:
        event.Event(type=ADMINS_UPDATED)

    if org_event:
        for org in organization.iter_orgs(fields=('_id')):
            event.Event(type=USERS_UPDATED, resource_id=org.id)

    event.Event(type=SETTINGS_UPDATED)

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
            settings.app.acme_timestamp = None
            settings.commit()
            return utils.jsonify({
                'error': ACME_ERROR,
                'error_msg': ACME_ERROR_MSG,
            }, 400)
    elif update_cert:
        logger.info('Regenerating server certificate...', 'handler')
        utils.create_server_cert()
        app.update_server(0.5)
    elif update_server:
        app.update_server(0.5)

    response = flask.g.administrator.dict()
    response.update(_dict())
    return utils.jsonify(response)

@app.app.route('/settings/zones', methods=['GET'])
@auth.session_auth
def settings_zones_get():
    return utils.jsonify(utils.get_zones())
