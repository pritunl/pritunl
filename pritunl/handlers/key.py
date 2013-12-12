from pritunl.constants import *
from pritunl.organization import Organization
import pritunl.utils as utils
from pritunl import app_server
import os
import flask
import uuid
import time

_key_ids = {}
_otp_ids = {}

def _get_key_archive(org_id, user_id):
    org = Organization(org_id)
    user = org.get_user(user_id)
    archive_temp_path = user.build_key_archive()

    with open(archive_temp_path, 'r') as archive_file:
        response = flask.Response(response=archive_file.read(),
            mimetype='application/x-tar')
        response.headers.add('Content-Disposition',
            'inline; filename="%s.tar"' % user.name)

    os.remove(archive_temp_path)
    return response

@app_server.app.route('/key/<org_id>/<user_id>.tar', methods=['GET'])
@app_server.auth
def user_key_archive_get(org_id, user_id):
    return _get_key_archive(org_id, user_id)

@app_server.app.route('/key/<org_id>/<user_id>', methods=['GET'])
@app_server.auth
def user_key_link_get(org_id, user_id):
    key_id = uuid.uuid4().hex
    otp_id = uuid.uuid4().hex
    _key_ids[key_id] = {
        'org_id': org_id,
        'user_id': user_id,
        'otp_id': otp_id,
        'timestamp': time.time(),
    }
    _otp_ids[otp_id] = {
        'org_id': org_id,
        'user_id': user_id,
        'key_id': key_id,
        'timestamp': time.time(),
    }
    return utils.jsonify({
        'id': key_id,
        'key_url': '/key/%s.tar' % key_id,
        'otp_url': '/key/%s.html' % otp_id,
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
    del _key_ids[key_id]
    return _get_key_archive(org_id, user_id)

@app_server.app.route('/key/<otp_id>.html', methods=['GET'])
def user_linked_key_page_get(otp_id):
    if otp_id not in _otp_ids:
        return flask.abort(404)
    elif time.time() - _otp_ids[otp_id]['timestamp'] > KEY_LINK_TIMEOUT:
        del _otp_ids[otp_id]
        return flask.abort(404)
    org_id = _otp_ids[otp_id]['org_id']
    user_id = _otp_ids[otp_id]['user_id']
    key_id = _otp_ids[otp_id]['key_id']
    del _otp_ids[otp_id]

    org = Organization(org_id)
    user = org.get_user(user_id)

    key_page = open(os.path.join(app_server.www_path,
        'key_index.html'), 'r').read()
    key_page = key_page.replace('<%= user_name %>', '%s - %s' % (
        org.name, user.name))
    key_page = key_page.replace('<%= user_otp_key %>', user.otp_secret)
    key_page = key_page.replace('<%= user_key_url %>', '/key/%s.tar' % (
        key_id))
    key_page = key_page.replace('<%= user_otp_url %>',
        'otpauth://totp/%s@%s?secret=%s' % (
            user.name, org.name, user.otp_secret))

    return key_page
