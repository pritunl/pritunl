from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import auth
from pritunl import utils
from pritunl import mongo
from pritunl import app
from pritunl import auth
from pritunl import event

import time
import flask
import bson

@app.app.route('/settings', methods=['GET'])
@auth.session_auth
def settings_get():
    response = flask.g.administrator.dict()
    response.update({
        'theme': settings.app.theme,
        'email_from': settings.app.email_from_addr,
        'email_api_key': settings.app.email_api_key,
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
        settings.app.email_from_addr = email_from or None
    if 'email_api_key' in flask.request.json:
        settings_commit = True
        email_api_key = flask.request.json['email_api_key']
        settings.app.email_api_key = email_api_key or None
    if 'theme' in flask.request.json:
        settings_commit = True
        theme = 'dark' if flask.request.json['theme'] == 'dark' else 'light'

        if theme != settings.app.theme:
            if theme == 'dark':
                event.Event(type=THEME_DARK)
            else:
                event.Event(type=THEME_LIGHT)

        settings.app.theme = theme

    if settings_commit:
        settings.commit()

    admin.commit(admin.changed)

    response = flask.g.administrator.dict()
    response.update({
        'email_from': settings.app.email_from_addr,
        'email_api_key': settings.app.email_api_key,
    })
    return utils.jsonify(response)

@app.app.route('/auth/session', methods=['POST'])
def auth_session_post():
    username = flask.request.json['username']
    password = flask.request.json['password']
    remote_addr = utils.get_remote_addr()
    admin = auth.check_auth(username, password, remote_addr)

    if not admin:
        return utils.jsonify({
            'error': AUTH_INVALID,
            'error_msg': AUTH_INVALID_MSG,
        }, 401)

    flask.session['session_id'] = admin.new_session()
    flask.session['admin_id'] = str(admin.id)
    flask.session['timestamp'] = int(time.time())
    if not settings.conf.ssl:
        flask.session['source'] = remote_addr

    return utils.jsonify({
        'authenticated': True,
        'default': admin.default,
    })

@app.app.route('/auth/session', methods=['DELETE'])
def auth_delete():
    admin_id = flask.session.get('admin_id')
    session_id = flask.session.get('session_id')
    if admin_id and session_id:
        admin_id = bson.ObjectId(admin_id)
        auth.clear_session(admin_id, session_id)
    flask.session.clear()

    return utils.jsonify({
        'authenticated': False,
    })
