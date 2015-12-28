from pritunl.constants import *
from pritunl import logger
from pritunl import utils
from pritunl import event
from pritunl import app
from pritunl import auth
from pritunl import settings

import flask

@app.app.route('/admin', methods=['GET'])
@app.app.route('/admin/<admin_id>', methods=['GET'])
@auth.session_auth
def admin_get(admin_id=None):
    if admin_id:
        return utils.jsonify(auth.get_by_id(admin_id).dict())

    admins = []

    for admin in auth.iter_admins():
        admins.append(admin.dict())

    return utils.jsonify(admins)
