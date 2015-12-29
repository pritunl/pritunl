from pritunl.constants import *
from pritunl import utils
from pritunl import event
from pritunl import app
from pritunl import auth

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

@app.app.route('/admin/<admin_id>', methods=['PUT'])
@auth.session_auth
def admin_put(admin_id):
    admin = auth.get_by_id(admin_id)

    if 'username' in flask.request.json:
        username = utils.filter_str(flask.request.json['username']) or None

        if username != admin.username:
            admin.audit_event('admin_updated',
                'Administrator username changed',
                remote_addr=utils.get_remote_addr(),
            )

        admin.username = username

    if 'password' in flask.request.json:
        password = flask.request.json['password']

        if password != admin.password:
            admin.audit_event('admin_updated',
                'Administrator password changed',
                remote_addr=utils.get_remote_addr(),
            )

        admin.password = password

    if 'token' in flask.request.json and flask.request.json['token']:
        admin.generate_token()
        admin.audit_event('admin_updated',
            'Administrator api token changed',
            remote_addr=utils.get_remote_addr(),
        )

    if 'secret' in flask.request.json and flask.request.json['secret']:
        admin.generate_secret()
        admin.audit_event('admin_updated',
            'Administrator api secret changed',
            remote_addr=utils.get_remote_addr(),
        )

    disabled = flask.request.json.get('disabled')
    if disabled is not None:
        if disabled != admin.disabled:
            admin.audit_event('admin_updated',
                'Administrator %s' % ('disabled' if disabled else 'enabled'),
                remote_addr=utils.get_remote_addr(),
            )

        admin.disabled = disabled

    otp_secret = flask.request.json.get('otp_secret')
    if otp_secret == True:
        admin.audit_event('admin_updated',
            'Administrator two-factor authentication secret reset',
            remote_addr=utils.get_remote_addr(),
        )
        admin.generate_otp_secret()

    admin.commit()
    event.Event(type=ADMINS_UPDATED)

    return utils.jsonify(admin.dict())

@app.app.route('/admin/<admin_id>/audit', methods=['GET'])
@auth.session_auth
def admin_audit_get(admin_id):
    admin = auth.get_by_id(admin_id)
    return utils.jsonify(admin.get_audit_events())
