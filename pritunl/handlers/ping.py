from pritunl import settings
from pritunl import utils
from pritunl import app
from pritunl import auth

import flask
import datetime

@app.app.route('/ping', methods=['GET'])
@app.app.route('/check', methods=['GET'])
@auth.open_auth
def ping_get():
    ping_timestamp = settings.local.host_ping_timestamp
    host_ping_ttl = datetime.timedelta(seconds=settings.app.host_ping_ttl)

    if ping_timestamp and utils.now() > ping_timestamp + host_ping_ttl:
        raise flask.abort(504)
    else:
        return utils.response(data='OK')
