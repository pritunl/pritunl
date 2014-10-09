from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import settings
from pritunl import utils
from pritunl import static
from pritunl import organization
from pritunl import settings
from pritunl import app
from pritunl import auth
from pritunl import mongo

import os
import flask
import uuid
import time
import random
import json

def _get_key_archive(org_id, user_id):
    org = organization.get_org(id=org_id)
    user = org.get_user(user_id)
    key_archive = user.build_key_archive()
    response = flask.Response(response=key_archive,
        mimetype='application/octet-stream')
    response.headers.add('Content-Disposition',
        'attachment; filename="%s.tar"' % user.name)
    return response

@app.app.route('/key/<org_id>/<user_id>.tar', methods=['GET'])
@auth.session_auth
def user_key_archive_get(org_id, user_id):
    return _get_key_archive(org_id, user_id)

@app.app.route('/key/<org_id>/<user_id>', methods=['GET'])
@auth.session_auth
def user_key_link_get(org_id, user_id):
    org = organization.get_org(id=org_id)
    return utils.jsonify(org.create_user_key_link(user_id))

@app.app.route('/key/<key_id>.tar', methods=['GET'])
def user_linked_key_archive_get(key_id):
    collection = mongo.get_collection('users_key_link')
    doc = collection.find_one({
        'key_id': key_id,
    })

    if not doc:
        time.sleep(settings.app.rate_limit_sleep)
        return flask.abort(404)

    return _get_key_archive(doc['org_id'], doc['user_id'])

@app.app.route('/k/<short_id>', methods=['GET'])
def user_linked_key_page_get(short_id):
    collection = mongo.get_collection('users_key_link')
    doc = collection.find_one({
        'short_id': short_id,
    })

    if not doc:
        time.sleep(settings.app.rate_limit_sleep)
        return flask.abort(404)

    org = organization.get_org(id=doc['org_id'])
    user = org.get_user(id=doc['user_id'])

    key_page = static.StaticFile(settings.conf.www_path, KEY_INDEX_NAME,
        cache=False).data
    key_page = key_page.replace('<%= user_name %>', '%s - %s' % (
        org.name, user.name))
    key_page = key_page.replace('<%= user_key_url %>', '/key/%s.tar' % (
        doc['key_id']))

    if org.otp_auth:
        key_page = key_page.replace('<%= user_otp_key %>', user.otp_secret)
        key_page = key_page.replace('<%= user_otp_url %>',
            'otpauth://totp/%s@%s?secret=%s' % (
                user.name, org.name, user.otp_secret))
    else:
        key_page = key_page.replace('<%= user_otp_key %>', '')
        key_page = key_page.replace('<%= user_otp_url %>', '')

    key_page = key_page.replace('<%= short_id %>', doc['short_id'])

    conf_links = ''
    for server in org.iter_servers():
        conf_links += '<a class="sm" title="Download Key" ' + \
            'href="/key/%s/%s.key">Download Key (%s)</a><br>\n' % (
                doc['key_id'], server.id, server.name)
    key_page = key_page.replace('<%= conf_links %>', conf_links)

    return key_page

@app.app.route('/k/<short_id>', methods=['DELETE'])
def user_linked_key_page_delete_get(short_id):
    collection = mongo.get_collection('users_key_link')
    collection.remove({
        'short_id': short_id,
    })
    return utils.jsonify({})

@app.app.route('/ku/<short_id>', methods=['GET'])
def user_uri_key_page_get(short_id):
    collection = mongo.get_collection('users_key_link')
    doc = collection.find_one({
        'short_id': short_id,
    })

    if not doc:
        time.sleep(settings.app.rate_limit_sleep)
        return flask.abort(404)

    org = organization.get_org(id=doc['org_id'])
    user = org.get_user(id=doc['user_id'])

    keys = {}
    for server in org.iter_servers():
        key = user.build_key_conf(server.id)
        keys[key['name']] = key['conf']

    return utils.jsonify(keys)

@app.app.route('/key/<key_id>/<server_id>.key', methods=['GET'])
def user_linked_key_conf_get(key_id, server_id):
    collection = mongo.get_collection('users_key_link')
    doc = collection.find_one({
        'key_id': key_id,
    })

    if not doc:
        time.sleep(settings.app.rate_limit_sleep)
        return flask.abort(404)

    org = organization.get_org(id=doc['org_id'])
    user = org.get_user(id=doc['user_id'])
    key_conf = user.build_key_conf(server_id)

    response = flask.Response(response=key_conf['conf'],
        mimetype='application/octet-stream')
    response.headers.add('Content-Disposition',
        'attachment; filename="%s"' % key_conf['name'])

    return response
