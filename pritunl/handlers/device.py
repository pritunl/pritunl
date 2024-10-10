from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import utils
from pritunl import app
from pritunl import auth
from pritunl import user
from pritunl import organization
from pritunl import settings
from pritunl import event
from pritunl import journal

import flask

@app.app.route('/device/unregistered', methods=['GET'])
@auth.session_auth
def device_unregistered_get():
    if settings.app.demo_mode:
        return utils.jsonify(DEMO_UNREGISTERED_DEVICES)

    devices = []

    for device in user.iter_unreg_devices():
        devices.append(device)

    return utils.jsonify(devices)

@app.app.route('/device/register/<org_id>/<user_id>/<device_id>',
    methods=['PUT'])
@auth.session_auth
def device_register_put(org_id, user_id, device_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    org = organization.get_by_id(org_id)
    usr = org.get_user(user_id)
    remote_addr = utils.get_remote_addr()
    reg_key = flask.request.json.get('reg_key')

    try:
        usr.device_register(device_id, reg_key)

        journal.entry(
            journal.USER_DEVICE_REGISTER_SUCCESS,
            usr.journal_data,
            device_id=device_id,
            remote_address=remote_addr,
            event_long='User device registered',
        )
    except DeviceNotFound:
        return utils.jsonify({
            'error': DEVICE_NOT_FOUND,
            'error_msg': DEVICE_NOT_FOUND_MSG,
        }, 400)
    except DeviceRegistrationLimit:
        event.Event(type=USERS_UPDATED, resource_id=org.id)
        event.Event(type=DEVICES_UPDATED, resource_id=org.id)

        journal.entry(
            journal.USER_DEVICE_REGISTER_FAILURE,
            usr.journal_data,
            device_id=device_id,
            remote_address=remote_addr,
            event_long='User device register failed, device limit',
        )

        return utils.jsonify({
            'error': DEVICE_REGISTRATION_LIMIT,
            'error_msg': DEVICE_REGISTRATION_LIMIT_MSG,
        }, 400)
    except DeviceRegistrationInvalid:
        event.Event(type=USERS_UPDATED, resource_id=org.id)
        event.Event(type=DEVICES_UPDATED, resource_id=org.id)

        journal.entry(
            journal.USER_DEVICE_REGISTER_FAILURE,
            usr.journal_data,
            device_id=device_id,
            remote_address=remote_addr,
            event_long='User device register failed, invalid code',
        )

        return utils.jsonify({
            'error': DEVICE_REGISTRATION_KEY_INVALID,
            'error_msg': DEVICE_REGISTRATION_KEY_INVALID_MSG,
        }, 400)

    event.Event(type=USERS_UPDATED, resource_id=org.id)
    event.Event(type=DEVICES_UPDATED, resource_id=org.id)

    return utils.jsonify({})

@app.app.route('/device/register/<org_id>/<user_id>/<device_id>',
    methods=['DELETE'])
@auth.session_auth
def device_register_delete(org_id, user_id, device_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    org = organization.get_by_id(org_id)
    usr = org.get_user(user_id)
    remote_addr = utils.get_remote_addr()

    try:
        usr.device_remove(device_id)
    except DeviceNotFound:
        return utils.jsonify({
            'error': DEVICE_NOT_FOUND,
            'error_msg': DEVICE_NOT_FOUND_MSG,
        }, 400)

    journal.entry(
        journal.USER_DEVICE_DELETE,
        usr.journal_data,
        device_id=device_id,
        remote_address=remote_addr,
        event_long='User device removed',
    )

    event.Event(type=USERS_UPDATED, resource_id=org.id)
    event.Event(type=DEVICES_UPDATED, resource_id=org.id)

    return utils.jsonify({})
