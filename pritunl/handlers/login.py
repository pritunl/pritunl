from pritunl.constants import *
import pritunl.utils as utils
from pritunl import app_server
import flask

@app_server.app.route('/login', methods=['POST'])
def login_post():
    username = flask.request.json['username']
    password = flask.request.json['password']

    if username != 'admin' or password != 'admin':
        return utils.jsonify({
            'error': AUTH_NOT_VALID,
            'error_msg': AUTH_NOT_VALID_MSG,
        }, 401)

    flask.session['id'] = app_server.session_id
    return utils.jsonify({})
