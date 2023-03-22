from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import utils
from pritunl import app
from pritunl import auth
from pritunl import user
from pritunl import organization
from pritunl import settings
from pritunl import event

import flask

@app.app.route('/device/unregistered', methods=['GET'])
@auth.session_auth
def device_unregistered_get():
    if settings.app.demo_mode:
        return utils.jsonify([]) # TODO

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

    reg_key = flask.request.json.get('reg_key')
    if not reg_key:
        return utils.jsonify({
            'error': DEVICE_NOT_FOUND,
            'error_msg': DEVICE_NOT_FOUND_MSG,
        }, 400)

    reg_key = reg_key.upper()

    try:
        usr.device_register(device_id, reg_key)
    except DeviceNotFound:
        return utils.jsonify({
            'error': DEVICE_NOT_FOUND,
            'error_msg': DEVICE_NOT_FOUND_MSG,
        }, 400)
    except DeviceRegistrationLimit:
        event.Event(type=USERS_UPDATED, resource_id=org.id)
        event.Event(type=DEVICES_UPDATED, resource_id=org.id)

        return utils.jsonify({
            'error': DEVICE_REGISTRATION_LIMIT,
            'error_msg': DEVICE_REGISTRATION_LIMIT_MSG,
        }, 400)
    except DeviceRegistrationInvalid:
        event.Event(type=USERS_UPDATED, resource_id=org.id)
        event.Event(type=DEVICES_UPDATED, resource_id=org.id)

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

    try:
        usr.device_remove(device_id)
    except DeviceNotFound:
        return utils.jsonify({
            'error': DEVICE_NOT_FOUND,
            'error_msg': DEVICE_NOT_FOUND_MSG,
        }, 400)

    event.Event(type=USERS_UPDATED, resource_id=org.id)
    event.Event(type=DEVICES_UPDATED, resource_id=org.id)

    return utils.jsonify({})
