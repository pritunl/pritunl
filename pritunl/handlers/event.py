from pritunl.helpers import *
from pritunl import utils
from pritunl import event
from pritunl import app
from pritunl import auth

import flask

@app.app.route('/event', methods=['GET'])
@app.app.route('/event/<cursor>', methods=['GET'])
@auth.session_auth
def event_get(cursor=None):
    if check_global_interrupt():
        raise flask.abort(500)

    if cursor is not None:
        cursor = utils.ObjectId(cursor)

    return utils.jsonify(event.get_events(
        cursor=cursor, yield_app_server=True))
