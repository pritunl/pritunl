from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import utils
from pritunl import app
from pritunl import subscription
from pritunl import settings
from pritunl import auth

import flask
import re
import httplib

@app.app.route('/subscription', methods=['GET'])
@auth.session_auth
def subscription_get():
    subscription.update()
    return utils.jsonify(subscription.dict())

@app.app.route('/subscription/state', methods=['GET'])
def subscription_state_get():
    return utils.jsonify({
        'active': settings.local.sub_active,
        'plan': settings.local.sub_plan,
    })

@app.app.route('/subscription', methods=['POST'])
@auth.session_auth
def subscription_post():
    license = flask.request.json['license']
    license = license.lower().replace('begin license', '').replace(
        'end license', '')
    license = re.sub(r'[\W_]+', '', license)

    try:
        response = utils.request.get(SUBSCRIPTION_SERVER,
            json_data={
                'license': license,
            },
        )
    except httplib.HTTPException:
        return utils.jsonify({
            'error': SUBSCRIPTION_SERVER_ERROR,
            'error_msg': SUBSCRIPTION_SERVER_ERROR_MSG,
        }, 500)
    data = response.json()

    if response.status_code != 200:
        return utils.jsonify(data, response.status_code)

    subscription.update_license(license)
    return utils.jsonify(subscription.dict())

@app.app.route('/subscription', methods=['PUT'])
@auth.session_auth
def subscription_put():
    card = flask.request.json.get('card')
    email = flask.request.json.get('email')
    plan = flask.request.json.get('plan')
    promo_code = flask.request.json.get('promo_code')
    cancel = flask.request.json.get('cancel')

    try:
        if cancel:
            response = utils.request.delete(SUBSCRIPTION_SERVER,
                json_data={
                    'license': settings.app.license,
                },
            )
        else:
            response = utils.request.put(SUBSCRIPTION_SERVER,
                json_data={
                    'license': settings.app.license,
                    'card': card,
                    'plan': plan,
                    'promo_code': promo_code,
                    'email': email,
                },
            )
    except httplib.HTTPException:
        return utils.jsonify({
            'error': SUBSCRIPTION_SERVER_ERROR,
            'error_msg': SUBSCRIPTION_SERVER_ERROR_MSG,
        }, 500)

    if response.status_code != 200:
        return utils.jsonify(response.json(), response.status_code)

    subscription.update()

    return utils.jsonify(subscription.dict())

@app.app.route('/subscription', methods=['DELETE'])
@auth.session_auth
def subscription_delete():
    subscription.update_license(None)
    return utils.jsonify({})
