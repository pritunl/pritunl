from pritunl.constants import *
from pritunl import utils
from pritunl import event
from pritunl.app_server import app_server
import time
import uuid
import flask

@app_server.app.route('/event', methods=['GET'])
@app_server.app.route('/event/<cursor>', methods=['GET'])
@app_server.auth
def event_get(cursor=None):
    if app_server.interrupt:
        return flask.abort(503)

    return utils.jsonify(event.get_events(cursor=cursor))
