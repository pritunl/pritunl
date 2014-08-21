from pritunl.constants import *
from pritunl.administrator import Administrator
from pritunl.settings import Settings
import pritunl.utils as utils
import pritunl.mongo as mongo
from pritunl import app_server
import time
import flask

@app_server.app.route('/auth', methods=['GET'])
@app_server.auth
def auth_get():
    settings = Settings()
    response = flask.request.administrator.dict()
    response.update(settings.dict())
    return utils.jsonify(response)

@app_server.app.route('/auth', methods=['PUT'])
@app_server.auth
def auth_put():
    administrator = flask.request.administrator
    settings = Settings()

    if 'username' in flask.request.json and flask.request.json['username']:
        administrator.username = utils.filter_str(
            flask.request.json['username'])
    if 'password' in flask.request.json and flask.request.json['password']:
        administrator.password = flask.request.json['password']
    if 'token' in flask.request.json and flask.request.json['token']:
        administrator.generate_token()
    if 'secret' in flask.request.json and flask.request.json['secret']:
        administrator.generate_secret()

    if 'email_from' in flask.request.json:
        email_from = flask.request.json['email_from']
        settings.set('email', 'from_addr', email_from or None)
    if 'email_api_key' in flask.request.json:
        email_api_key = flask.request.json['email_api_key']
        settings.set('email', 'api_key', email_api_key or None)

    settings.commit()
    administrator.commit()

    response = flask.request.administrator.dict()
    response.update(settings.dict())
    return utils.jsonify(response)

@app_server.app.route('/auth/session', methods=['GET'])
def auth_get():
    return utils.jsonify({
        'authenticated': Administrator.check_session(),
    })

@app_server.app.route('/auth/session', methods=['POST'])
def auth_session_post():
    username = flask.request.json['username']
    password = flask.request.json['password']
    remote_addr = utils.get_remote_addr()
    administrator = Administrator.check_auth(username, password, remote_addr)

    if not administrator:
        return utils.jsonify({
            'error': AUTH_INVALID,
            'error_msg': AUTH_INVALID_MSG,
        }, 401)

    flask.session['admin_id'] = administrator.id
    flask.session['time'] = int(time.time())
    if not app_server.ssl:
        flask.session['source'] = remote_addr

    return utils.jsonify({
        'authenticated': True,
        'default': administrator.default,
    })

@app_server.app.route('/auth/session', methods=['DELETE'])
def auth_delete():
    flask.session.clear()
    return utils.jsonify({
        'authenticated': False,
    })
