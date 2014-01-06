from pritunl.constants import *
from pritunl.organization import Organization
import pritunl.utils as utils
from pritunl import app_server
import os
import flask
import uuid
import time
import random
import string

_key_ids = {}
_view_ids = {}
_conf_ids = {}

def _get_key_archive(org_id, user_id):
    org = Organization(org_id)
    user = org.get_user(user_id)
    archive_temp_path = user.build_key_archive()

    with open(archive_temp_path, 'r') as archive_file:
        response = flask.Response(response=archive_file.read(),
            mimetype='application/octet-stream')
        response.headers.add('Content-Disposition',
            'attachment; filename="%s.tar"' % user.name)

    os.remove(archive_temp_path)
    return response

@app_server.app.route('/key/<org_id>/<user_id>.tar', methods=['GET'])
@app_server.auth
def user_key_archive_get(org_id, user_id):
    return _get_key_archive(org_id, user_id)

@app_server.app.route('/key/<org_id>/<user_id>', methods=['GET'])
@app_server.auth
def user_key_link_get(org_id, user_id):
    org = Organization(org_id)
    servers = org.get_servers()
    key_id = uuid.uuid4().hex
    view_id = ''.join(random.sample(
        string.ascii_lowercase + string.ascii_uppercase + string.digits, 5))

    _key_ids[key_id] = {
        'org_id': org_id,
        'user_id': user_id,
        'view_id': view_id,
        'timestamp': time.time(),
        'count': 0,
    }

    conf_urls = []
    if app_server.inline_certs:
        for server in servers:
            conf_id = uuid.uuid4().hex
            _conf_ids[conf_id] = {
                'org_id': org_id,
                'user_id': user_id,
                'server_id': server.id,
                'timestamp': time.time(),
                'count': 0,
            }
            conf_urls.append({
                'server_name': server.name,
                'url': '/key/%s.ovpn' % conf_id,
            })

    _view_ids[view_id] = {
        'org_id': org_id,
        'user_id': user_id,
        'key_id': key_id,
        'timestamp': time.time(),
        'conf_urls': conf_urls,
    }

    return utils.jsonify({
        'id': key_id,
        'key_url': '/key/%s.tar' % key_id,
        'view_url': '/key/%s' % view_id,
    })

@app_server.app.route('/key/<key_id>.tar', methods=['GET'])
def user_linked_key_archive_get(key_id):
    if key_id not in _key_ids:
        return flask.abort(404)
    elif time.time() - _key_ids[key_id]['timestamp'] > KEY_LINK_TIMEOUT:
        del _key_ids[key_id]
        return flask.abort(404)
    org_id = _key_ids[key_id]['org_id']
    user_id = _key_ids[key_id]['user_id']

    # Fix for android sending two GET requests when downloading
    _key_ids[key_id]['count'] += 1
    if _key_ids[key_id]['count'] >= 2:
        del _key_ids[key_id]

    return _get_key_archive(org_id, user_id)

@app_server.app.route('/key/<view_id>', methods=['GET'])
def user_linked_key_page_get(view_id):
    if view_id not in _view_ids:
        return flask.abort(404)
    elif time.time() - _view_ids[view_id]['timestamp'] > KEY_LINK_TIMEOUT:
        del _view_ids[view_id]
        return flask.abort(404)
    org_id = _view_ids[view_id]['org_id']
    user_id = _view_ids[view_id]['user_id']
    key_id = _view_ids[view_id]['key_id']
    conf_urls = _view_ids[view_id]['conf_urls']
    del _view_ids[view_id]

    org = Organization(org_id)
    user = org.get_user(user_id)

    key_page = open(os.path.join(app_server.www_path,
        'key_index.html'), 'r').read()
    key_page = key_page.replace('<%= user_name %>', '%s - %s' % (
        org.name, user.name))
    key_page = key_page.replace('<%= user_key_url %>', '/key/%s.tar' % (
        key_id))

    if org.otp_auth:
        key_page = key_page.replace('<%= user_otp_key %>', user.otp_secret)
        key_page = key_page.replace('<%= user_otp_url %>',
            'otpauth://totp/%s@%s?secret=%s' % (
                user.name, org.name, user.otp_secret))
    else:
        key_page = key_page.replace('<%= user_otp_key %>', '')
        key_page = key_page.replace('<%= user_otp_url %>', '')

    if app_server.inline_certs:
        conf_links = ''
        for conf_url in conf_urls:
            conf_links += '<a class="sm" title="Download Mobile Key" ' + \
                'href="%s">Download Mobile Key (%s)</a><br>\n' % (
                    conf_url['url'], conf_url['server_name'])
        key_page = key_page.replace('<%= conf_links %>', conf_links)

    return key_page

@app_server.app.route('/key/<conf_id>.ovpn', methods=['GET'])
def user_linked_key_conf_get(conf_id):
    if conf_id not in _conf_ids:
        return flask.abort(404)
    elif time.time() - _conf_ids[conf_id]['timestamp'] > KEY_LINK_TIMEOUT:
        del _conf_ids[conf_id]
        return flask.abort(404)
    org_id = _conf_ids[conf_id]['org_id']
    user_id = _conf_ids[conf_id]['user_id']
    server_id = _conf_ids[conf_id]['server_id']

    # Fix for android sending two GET requests when downloading
    _conf_ids[conf_id]['count'] += 1
    if _conf_ids[conf_id]['count'] >= 2:
        del _conf_ids[conf_id]

    org = Organization(org_id)
    user = org.get_user(user_id)
    key_conf = user.build_key_conf(server_id)

    response = flask.Response(response=key_conf['conf'],
        mimetype='application/octet-stream')
    response.headers.add('Content-Disposition',
        'attachment; filename="%s"' % key_conf['name'])

    return response
