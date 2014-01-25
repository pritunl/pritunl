from pritunl.constants import *
from pritunl.auth_token import AuthToken
import pritunl.utils as utils
from pritunl import app_server
import time
import flask

@app_server.app.route('/auth', methods=['POST'])
def auth_post():
    username = flask.request.json['username'][:512]
    password = flask.request.json['password'][:512]

    if username != AUTH_USER_NAME or not app_server.check_password(password):
        time.sleep(RATE_LIMIT_SLEEP)
        return utils.jsonify({
            'error': AUTH_INVALID,
            'error_msg': AUTH_INVALID_MSG,
        }, 401)

    flask.session['timestamp'] = time.time()
    return utils.jsonify({
        'authenticated': True,
    })

@app_server.app.route('/auth', methods=['GET'])
def auth_get():
    authenticated = False
    auth_token = flask.request.headers.get('Auth-Token', None)
    if auth_token:
        auth_token = AuthToken(auth_token)
        if auth_token.valid:
            authenticated = True
    elif 'timestamp' in flask.session:
        authenticated = True
    return utils.jsonify({
        'authenticated': authenticated,
    })

@app_server.app.route('/auth', methods=['DELETE'])
def auth_delete():
    flask.session.pop('timestamp', None)
    return utils.jsonify({
        'authenticated': False,
    })

@app_server.app.route('/auth/token', methods=['POST'])
def auth_token_post():
    username = flask.request.json['username'][:512]
    password = flask.request.json['password'][:512]

    if username != AUTH_USER_NAME or not app_server.check_password(password):
        time.sleep(RATE_LIMIT_SLEEP)
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
