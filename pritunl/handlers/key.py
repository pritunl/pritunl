from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.organization import Organization
from pritunl.static_file import StaticFile
import pritunl.utils as utils
from pritunl.cache import cache_db
from pritunl import app_server
import os
import flask
import uuid
import time
import random
import json

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
    return utils.jsonify(org.create_user_key_link(user_id))

@app_server.app.route('/key/<key_id>.tar', methods=['GET'])
def user_linked_key_archive_get(key_id):
    key_id_key = 'key_token-%s' % key_id
    org_id = cache_db.dict_get(key_id_key, 'org_id')
    user_id = cache_db.dict_get(key_id_key, 'user_id')

    # Check for expire
    if not cache_db.exists(key_id_key):
        time.sleep(RATE_LIMIT_SLEEP)
        return flask.abort(404)

    return _get_key_archive(org_id, user_id)

@app_server.app.route('/k/<view_id>', methods=['GET'])
def user_linked_key_page_get(view_id):
    view_id_key = 'view_token-%s' % view_id
    org_id = cache_db.dict_get(view_id_key, 'org_id')
    user_id = cache_db.dict_get(view_id_key, 'user_id')
    key_id = cache_db.dict_get(view_id_key, 'key_id')
    conf_urls = cache_db.dict_get(view_id_key, 'conf_urls')
    if conf_urls:
        conf_urls = json.loads(conf_urls)

    # Check for expire
    if not cache_db.exists(view_id_key):
        time.sleep(RATE_LIMIT_SLEEP)
        return flask.abort(404)

    org = Organization.get_org(id=org_id)
    user = org.get_user(user_id)

    key_page = StaticFile(app_server.www_path, KEY_INDEX_NAME,
        cache=False).data
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

    key_page = key_page.replace('<%= view_id %>', view_id)

    conf_links = ''
    for conf_url in conf_urls:
        conf_links += '<a class="sm" title="Download Mobile Key" ' + \
            'href="%s">Download Mobile Key (%s)</a><br>\n' % (
                conf_url['url'], conf_url['server_name'])
    key_page = key_page.replace('<%= conf_links %>', conf_links)

    return key_page

@app_server.app.route('/k/<view_id>', methods=['DELETE'])
def user_linked_key_page_delete_get(view_id):
    view_id_key = 'view_token-%s' % view_id

    key_id = cache_db.dict_get(view_id_key, 'key_id')
    if key_id:
        cache_db.remove('key_token-%s' % key_id)

    uri_id = cache_db.dict_get(view_id_key, 'uri_id')
    if uri_id:
        cache_db.remove('uri_token-%s' % uri_id)

    conf_urls = cache_db.dict_get(view_id_key, 'conf_urls')
    if conf_urls:
        for conf_url in json.loads(conf_urls):
            cache_db.remove('conf_token-%s' % conf_url['id'])

    cache_db.remove(view_id_key)
    return utils.jsonify({})

@app_server.app.route('/ku/<uri_id>', methods=['GET'])
def user_uri_key_page_get(uri_id):
    uri_id_key = 'uri_token-%s' % uri_id
    org_id = cache_db.dict_get(uri_id_key, 'org_id')
    user_id = cache_db.dict_get(uri_id_key, 'user_id')

    # Check for expire
    if not cache_db.exists(uri_id_key):
        time.sleep(RATE_LIMIT_SLEEP)
        return flask.abort(404)

    org = Organization.get_org(id=org_id)
    user = org.get_user(user_id)

    keys = {}
    for server in org.iter_servers():
        key = user.build_key_conf(server.id)
        keys[key['name']] = key['conf']

    return utils.jsonify(keys)

@app_server.app.route('/key/<conf_id>.ovpn', methods=['GET'])
def user_linked_key_conf_get(conf_id):
    conf_id_key = 'conf_token-%s' % conf_id
    org_id = cache_db.dict_get(conf_id_key, 'org_id')
    user_id = cache_db.dict_get(conf_id_key, 'user_id')
    server_id = cache_db.dict_get(conf_id_key, 'server_id')

    # Check for expire
    if not cache_db.exists(conf_id_key):
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
