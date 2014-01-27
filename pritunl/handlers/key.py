from pritunl.constants import *
from pritunl.organization import Organization
import pritunl.utils as utils
from pritunl.cache import cache_db
from pritunl import app_server
import os
import flask
import uuid
import time
import random
import json

def _get_key_key(key_id):
    return 'key_token-%s' % key_id

def _get_view_key(key_id):
    return 'view_token-%s' % key_id

def _get_conf_key(key_id):
    return 'conf_token-%s' % key_id

def _get_key_archive(org_id, user_id):
    org = Organization.get_org(id=org_id)
    user = org.get_user(user_id)
    archive_temp_path = user.build_key_archive()
    try:
        with open(archive_temp_path, 'r') as archive_file:
            response = flask.Response(response=archive_file.read(),
                mimetype='application/octet-stream')
            response.headers.add('Content-Disposition',
                'attachment; filename="%s.tar"' % user.name)
    finally:
        user.clean_key_archive()
    return response

@app_server.app.route('/key/<org_id>/<user_id>.tar', methods=['GET'])
@app_server.auth
def user_key_archive_get(org_id, user_id):
    return _get_key_archive(org_id, user_id)

@app_server.app.route('/key/<org_id>/<user_id>', methods=['GET'])
@app_server.auth
def user_key_link_get(org_id, user_id):
    org = Organization.get_org(id=org_id)
    key_id = uuid.uuid4().hex

    view_id = None
    for i in xrange(2048):
        temp_view_id = ''.join(random.sample(SHORT_URL_CHARS, SHORT_URL_LEN))
        if not cache_db.exists(_get_view_key(temp_view_id)):
            view_id = temp_view_id
            break
    if not view_id:
        raise AttributeError('Failed to generate random view id')

    cache_db.expire(_get_key_key(key_id), KEY_LINK_TIMEOUT)
    cache_db.dict_set(_get_key_key(key_id), 'org_id', org_id)
    cache_db.dict_set(_get_key_key(key_id), 'user_id', user_id)
    cache_db.dict_set(_get_key_key(key_id), 'view_id', view_id)

    conf_urls = []
    if app_server.inline_certs:
        for server in org.iter_servers():
            conf_id = uuid.uuid4().hex

            cache_db.expire(_get_conf_key(conf_id), KEY_LINK_TIMEOUT)
            cache_db.dict_set(_get_conf_key(conf_id), 'org_id', org_id)
            cache_db.dict_set(_get_conf_key(conf_id), 'user_id', user_id)
            cache_db.dict_set(_get_conf_key(conf_id), 'server_id', server.id)

            conf_urls.append({
                'server_name': server.name,
                'url': '/key/%s.ovpn' % conf_id,
            })

    cache_db.expire(_get_view_key(view_id), KEY_LINK_TIMEOUT)
    cache_db.dict_set(_get_view_key(view_id), 'org_id', org_id)
    cache_db.dict_set(_get_view_key(view_id), 'user_id', user_id)
    cache_db.dict_set(_get_view_key(view_id), 'key_id', key_id)
    cache_db.dict_set(_get_view_key(view_id),
        'conf_urls', json.dumps(conf_urls))

    return utils.jsonify({
        'id': key_id,
        'key_url': '/key/%s.tar' % key_id,
        'view_url': '/k/%s' % view_id,
    })

@app_server.app.route('/key/<key_id>.tar', methods=['GET'])
def user_linked_key_archive_get(key_id):
    org_id = cache_db.dict_get(_get_key_key(key_id), 'org_id')
    user_id = cache_db.dict_get(_get_key_key(key_id), 'user_id')

    # Check for expire
    if not cache_db.exists(_get_key_key(key_id)):
        time.sleep(RATE_LIMIT_SLEEP)
        return flask.abort(404)

    return _get_key_archive(org_id, user_id)

@app_server.app.route('/k/<view_id>', methods=['GET'])
def user_linked_key_page_get(view_id):
    org_id = cache_db.dict_get(_get_view_key(view_id), 'org_id')
    user_id = cache_db.dict_get(_get_view_key(view_id), 'user_id')
    key_id = cache_db.dict_get(_get_view_key(view_id), 'key_id')
    conf_urls = cache_db.dict_get(_get_view_key(view_id), 'conf_urls')
    if conf_urls:
        conf_urls = json.loads(conf_urls)

    # Check for expire
    if not cache_db.exists(_get_view_key(view_id)):
        time.sleep(RATE_LIMIT_SLEEP)
        return flask.abort(404)

    org = Organization.get_org(id=org_id)
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

    conf_links = ''
    for conf_url in conf_urls:
        conf_links += '<a class="sm" title="Download Mobile Key" ' + \
            'href="%s">Download Mobile Key (%s)</a><br>\n' % (
                conf_url['url'], conf_url['server_name'])
    key_page = key_page.replace('<%= conf_links %>', conf_links)

    return key_page

@app_server.app.route('/key/<conf_id>.ovpn', methods=['GET'])
def user_linked_key_conf_get(conf_id):
    org_id = cache_db.dict_get(_get_conf_key(conf_id), 'org_id')
    user_id = cache_db.dict_get(_get_conf_key(conf_id), 'user_id')
    server_id = cache_db.dict_get(_get_conf_key(conf_id), 'server_id')

    # Check for expire
    if not cache_db.exists(_get_conf_key(conf_id)):
        time.sleep(RATE_LIMIT_SLEEP)
        return flask.abort(404)

    org = Organization.get_org(id=org_id)
    user = org.get_user(user_id)
    key_conf = user.build_key_conf(server_id)

    response = flask.Response(response=key_conf['conf'],
        mimetype='application/octet-stream')
    response.headers.add('Content-Disposition',
        'attachment; filename="%s"' % key_conf['name'])

    return response
