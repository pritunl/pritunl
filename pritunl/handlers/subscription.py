from pritunl.constants import *
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
@auth.session_auth
def subscription_state_get():
    return utils.jsonify({
        'super_user': flask.g.administrator.super_user,
        'theme': settings.app.theme,
        'active': settings.local.sub_active,
        'plan': settings.local.sub_plan,
        'version': settings.local.version_int,
        'sso': settings.app.sso,
    })

@app.app.route('/subscription/styles/<plan>/<ver>.css', methods=['GET'])
@auth.session_auth
def subscription_styles_get(plan, ver):
    try:
        styles = settings.local.sub_styles[plan]
    except KeyError:
        subscription.update()
        styles = settings.local.sub_styles[plan]

    return utils.styles_response(
        styles['etag'],
        styles['last_modified'],
        styles['data'],
    )

@app.app.route('/subscription', methods=['POST'])
@auth.session_auth
def subscription_post():
    if settings.app.demo_mode:
        return utils.demo_blocked()

    license = flask.request.json['license']
    license = license.lower().replace('begin license', '').replace(
        'end license', '')
    license = re.sub(r'[\W_]+', '', license)

    try:
        response = utils.request.get(
            'https://app.pritunl.com/subscription',
            json_data={
                'license': license,
                'version': settings.local.version_int,
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
    if settings.app.demo_mode:
        return utils.demo_blocked()

    card = flask.request.json.get('card')
    email = flask.request.json.get('email')
    plan = flask.request.json.get('plan')
    promo_code = flask.request.json.get('promo_code')
    cancel = flask.request.json.get('cancel')

    try:
        if cancel:
            response = utils.request.delete(
                'https://app.pritunl.com/subscription',
                json_data={
                    'license': settings.app.license,
                },
            )
        else:
            response = utils.request.put(
                'https://app.pritunl.com/subscription',
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
    if settings.app.demo_mode:
        return utils.demo_blocked()

    subscription.update_license(None)
    return utils.jsonify({})
