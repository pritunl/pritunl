from pritunl.constants import *
import pritunl.utils as utils
from pritunl import app_server
import flask

@app_server.app.route('/password', methods=['PUT'])
@app_server.auth
def password_put():
    username = flask.request.json['username'] or "admin" if 'username' in flask.request.json else "admin"
    password = flask.request.json['password']
    app_server.set_password(username, password)
    return utils.jsonify({
        'username': username,
        'password': password,
    })
