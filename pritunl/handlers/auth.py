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
    time.sleep(AUTH_BRUTE_FORCE_SLEEP)

    if username != AUTH_USER_NAME or not app_server.check_password(password):
        time.sleep(AUTH_BRUTE_FORCE_SLEEP)
        return utils.jsonify({
            'error': AUTH_NOT_VALID,
            'error_msg': AUTH_NOT_VALID_MSG,
        }, 401)

    flask.session['timestamp'] = time.time()
    return utils.jsonify({
        'authenticated': True,
    })

@app_server.app.route('/auth', methods=['GET'])
def auth_get():
    authenticated = False
    if 'timestamp' in flask.session:
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
    time.sleep(AUTH_BRUTE_FORCE_SLEEP)

    if username != AUTH_USER_NAME or not app_server.check_password(password):
        time.sleep(AUTH_BRUTE_FORCE_SLEEP)
        return utils.jsonify({
            'error': AUTH_NOT_VALID,
            'error_msg': AUTH_NOT_VALID_MSG,
        }, 401)

    auth_token = AuthToken()
    return utils.jsonify({
        'auth_token': auth_token.id,
    })

@app_server.app.route('/auth/token/<auth_token>', methods=['DELETE'])
def auth_token_delete(auth_token):
    auth_token = AuthToken(auth_token)
    auth_token.delete()
    return utils.jsonify({})
