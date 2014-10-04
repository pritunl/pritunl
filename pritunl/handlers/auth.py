from pritunl.constants import *
from pritunl.settings import settings
from pritunl import administrator
from pritunl import utils
from pritunl import mongo
from pritunl.app_server import app_server
import time
import flask

@app_server.app.route('/auth', methods=['GET'])
@app_server.auth
def auth_get():
    response = flask.g.administrator.dict()
    response.update({
        'email_from': settings.app.email_from_addr,
        'email_api_key': settings.app.email_api_key,
    })
    return utils.jsonify(response)

@app_server.app.route('/auth', methods=['PUT'])
@app_server.auth
def auth_put():
    admin = flask.g.administrator

    if 'username' in flask.request.json and flask.request.json['username']:
        admin.username = utils.filter_str(
            flask.request.json['username'])
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
    if settings_commit:
        settings.commit()

    admin.commit(admin.changed)

    response = flask.g.administrator.dict()
    response.update({
        'email_from': settings.app.email_from_addr,
        'email_api_key': settings.app.email_api_key,
    })
    return utils.jsonify(response)

@app_server.app.route('/auth/session', methods=['GET'])
def auth_get():
    return utils.jsonify({
        'authenticated': administrator.check_session(),
    })

@app_server.app.route('/auth/session', methods=['POST'])
def auth_session_post():
    username = flask.request.json['username']
    password = flask.request.json['password']
    remote_addr = utils.get_remote_addr()
    admin = administrator.check_auth(username, password, remote_addr)

    if not admin:
        return utils.jsonify({
            'error': AUTH_INVALID,
            'error_msg': AUTH_INVALID_MSG,
        }, 401)

    flask.session['admin_id'] = admin.id
    flask.session['timestamp'] = int(time.time())
    if not app_server.ssl:
        flask.session['source'] = remote_addr

    return utils.jsonify({
        'authenticated': True,
        'default': admin.default,
    })

@app_server.app.route('/auth/session', methods=['DELETE'])
def auth_delete():
    flask.session.clear()
    return utils.jsonify({
        'authenticated': False,
    })
