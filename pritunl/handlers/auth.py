from pritunl.constants import *
from pritunl.auth_token import AuthToken
import pritunl.utils as utils
from pritunl import app_server
import time
import flask

@app_server.app.route('/auth', methods=['PUT'])
@app_server.auth
def auth_put():
    username = utils.filter_str(flask.request.json.get('username'))
    password = flask.request.json['password']

    utils.set_auth(username, password)
    return utils.jsonify({
        'username': utils.get_auth(),
    })

@app_server.app.route('/auth/session', methods=['GET'])
def auth_get():
    return utils.jsonify({
        'authenticated': utils.check_session(),
    })

@app_server.app.route('/auth/session', methods=['POST'])
def auth_session_post():
    username = flask.request.json['username']
    password = flask.request.json['password']
    remote_addr = utils.get_remote_addr()

    if not utils.check_auth(username, password, remote_addr):
        return utils.jsonify({
            'error': AUTH_INVALID,
            'error_msg': AUTH_INVALID_MSG,
        }, 401)

    flask.session['auth'] = True
    flask.session['timestamp'] = int(time.time())
    if not app_server.ssl:
        flask.session['source'] = remote_addr

    data = {
        'authenticated': True,
    }
    if password == DEFAULT_PASSWORD:
        data['default_password'] = True
    return utils.jsonify(data)

@app_server.app.route('/auth/session', methods=['DELETE'])
def auth_delete():
    flask.session.clear()
    return utils.jsonify({
        'authenticated': False,
    })

@app_server.app.route('/auth/token', methods=['POST'])
def auth_token_post():
    username = flask.request.json['username']
    password = flask.request.json['password']
    remote_addr = utils.get_remote_addr()

    if not utils.check_auth(username, password, remote_addr):
        return utils.jsonify({
            'error': AUTH_INVALID,
            'error_msg': AUTH_INVALID_MSG,
        }, 401)

    auth_token = AuthToken()
    return utils.jsonify({
        'auth_token': auth_token.id,
    })

@app_server.app.route('/auth/token/<auth_token>', methods=['DELETE'])
def auth_token_delete(auth_token):
    auth_token = AuthToken(auth_token)
    auth_token.remove()
    return utils.jsonify({})
