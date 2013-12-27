from pritunl.constants import *
import pritunl.utils as utils
from pritunl import app_server
import time
import flask

@app_server.app.route('/auth', methods=['POST'])
def auth_post():
    username = flask.request.json['username'][:512]
    password = flask.request.json['password'][:512]
    time.sleep(0.5)

    if username != 'admin' or not app_server.check_password(password):
        time.sleep(0.5)
        return utils.jsonify({
            'error': AUTH_NOT_VALID,
            'error_msg': AUTH_NOT_VALID_MSG,
        }, 401)

    flask.session['timestamp'] = time.time()
    return utils.jsonify({})

@app_server.app.route('/auth', methods=['GET'])
def auth_get():
    authenticated = False
    if 'timestamp' in flask.session:
        authenticated = True
    return utils.jsonify({
        'authenticated': authenticated
    })

@app_server.app.route('/auth', methods=['DELETE'])
def auth_delete():
    flask.session.pop('timestamp', None)
    return utils.jsonify({})
