from pritunl.constants import *
import pritunl.utils as utils
from pritunl import app_server
import flask

@app_server.app.route('/auth', methods=['POST'])
def auth_post():
    username = flask.request.json['username']
    password = flask.request.json['password']

    if username != 'admin' or password != 'admin':
        return utils.jsonify({
            'error': AUTH_NOT_VALID,
            'error_msg': AUTH_NOT_VALID_MSG,
        }, 401)

    flask.session['id'] = app_server.session_id
    return utils.jsonify({})

@app_server.app.route('/auth', methods=['GET'])
def auth_get():
    authenticated = False
    if 'id' in flask.session and flask.session['id'] == self.session_id:
        authenticated = True
    return utils.jsonify({
        'authenticated': authenticated
    })

@app_server.app.route('/auth', methods=['DELETE'])
def auth_delete():
    flask.session.pop('id', None)
    return utils.jsonify({})
