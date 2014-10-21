from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import utils
from pritunl import event
from pritunl import app
from pritunl import auth

import time
import uuid
import flask
import bson

@app.app.route('/event', methods=['GET'])
@app.app.route('/event/<cursor>', methods=['GET'])
@auth.session_auth
def event_get(cursor=None):
    if cursor is not None:
        cursor = bson.ObjectId(cursor)

    return utils.jsonify(event.get_events(cursor=cursor))
