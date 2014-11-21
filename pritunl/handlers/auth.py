from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import auth
from pritunl import utils
from pritunl import mongo
from pritunl import app
from pritunl import auth
from pritunl import event

import time
import flask
import bson

@app.app.route('/auth/session', methods=['POST'])
def auth_session_post():
    username = flask.request.json['username']
    password = flask.request.json['password']
    remote_addr = utils.get_remote_addr()
    admin = auth.check_auth(username, password, remote_addr)

    if not admin:
        return utils.jsonify({
            'error': AUTH_INVALID,
            'error_msg': AUTH_INVALID_MSG,
        }, 401)

    flask.session['session_id'] = admin.new_session()
    flask.session['admin_id'] = str(admin.id)
    flask.session['timestamp'] = int(time.time())
    if not settings.conf.ssl:
        flask.session['source'] = remote_addr

    return utils.jsonify({
        'authenticated': True,
        'default': admin.default,
    })

@app.app.route('/auth/session', methods=['DELETE'])
def auth_delete():
    admin_id = flask.session.get('admin_id')
    session_id = flask.session.get('session_id')
    if admin_id and session_id:
        admin_id = bson.ObjectId(admin_id)
        auth.clear_session(admin_id, session_id)
    flask.session.clear()

    return utils.jsonify({
        'authenticated': False,
    })
