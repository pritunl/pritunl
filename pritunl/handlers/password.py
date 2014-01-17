from pritunl.constants import *
import pritunl.utils as utils
from pritunl import app_server
import flask

@app_server.app.route('/password', methods=['PUT'])
@app_server.auth
def password_put():
    password = flask.request.json['password'][:512]
    app_server.set_password(password)
    return utils.jsonify({
        'password': password,
    })
