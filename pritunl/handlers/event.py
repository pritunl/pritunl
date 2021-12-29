from pritunl.helpers import *
from pritunl import utils
from pritunl import event
from pritunl import app
from pritunl import auth
from pritunl import settings
from pritunl import database

import flask
import time

@app.app.route('/event', methods=['GET'])
@app.app.route('/event/<cursor>', methods=['GET'])
@auth.session_auth
def event_get(cursor=None):
    if settings.app.demo_mode:
        time.sleep(0.1)
        return utils.jsonify([{
            'id': 'demo',
        }])

    if check_global_interrupt():
        raise flask.abort(500)

    if cursor is not None:
        cursor = database.ParseObjectId(cursor)

    return utils.jsonify(event.get_events(
        cursor=cursor, yield_app_server=True))
