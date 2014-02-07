from pritunl.constants import *
from pritunl.auth_token import AuthToken
import pritunl.utils as utils
from pritunl import app_server
import time
import flask

@app_server.app.route('/auth', methods=['POST'])
def auth_post():
    username = flask.request.json['username']
    password = flask.request.json['password']
    remote_addr = utils.get_remote_addr()

    if not app_server.check_account(username, password, remote_addr):
        return utils.jsonify({
            'error': AUTH_INVALID,
            'error_msg': AUTH_INVALID_MSG,
        }, 401)

    flask.session['auth'] = True
    flask.session['timestamp'] = int(time.time())
    if not app_server.ssl:
        flask.session['source'] = remote_addr
    return utils.jsonify({
        'authenticated': True,
    })

@app_server.app.route('/auth', methods=['GET'])
def auth_get():
    return utils.jsonify({
        'authenticated': utils.check_auth(),
    })

@app_server.app.route('/auth', methods=['DELETE'])
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

    if not app_server.check_account(username, password, remote_addr):
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
