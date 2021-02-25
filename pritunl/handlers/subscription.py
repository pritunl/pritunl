from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import utils
from pritunl import app
from pritunl import subscription
from pritunl import settings
from pritunl import auth

import flask
import re
import http.client
import requests

@app.app.route('/subscription', methods=['GET'])
@auth.session_auth
def subscription_get():
    if settings.app.demo_mode:
        resp = utils.demo_get_cache()
        if resp:
            return utils.jsonify(resp)

    subscription.update()
    resp = subscription.dict()
    if settings.app.demo_mode:
        utils.demo_set_cache(resp)
    return utils.jsonify(resp)

@app.app.route('/subscription/styles/<plan>/<ver>.css', methods=['GET'])
@auth.session_light_auth
def subscription_styles_get(plan, ver):
    try:
        styles = settings.local.sub_styles[plan]
    except KeyError:
        subscription.update()
        try:
                styles = settings.local.sub_styles[plan]
        except KeyError:
                styles = {'etag' : 0, 'last_modified' : 0, 'data' : ''}

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
        url = 'https://app.pritunl.com/subscription'
        if settings.app.dedicated:
            url = settings.app.dedicated + '/subscription'

        response = requests.get(
            url,
            json={
                'license': license,
                'version': settings.local.version_int,
            },
        )
    except http.client.HTTPException:
        return utils.jsonify({
            'error': SUBSCRIPTION_SERVER_ERROR,
            'error_msg': SUBSCRIPTION_SERVER_ERROR_MSG,
        }, 500)
    data = response.json()

    if response.status_code != 200:
        return utils.jsonify(data, response.status_code)

    try:
        subscription.update_license(license)
    except LicenseInvalid:
        return utils.jsonify({
            'error': LICENSE_INVALID,
            'error_msg': LICENSE_INVALID_MSG,
        }, 500)
    return utils.jsonify(subscription.dict())

@app.app.route('/subscription', methods=['PUT'])
@auth.session_auth
def subscription_put():
    if settings.app.demo_mode:
        return utils.demo_blocked()

    card = flask.request.json.get('card')
    email = flask.request.json.get('email')
    plan = flask.request.json.get('plan')
    cancel = flask.request.json.get('cancel')

    try:
        url = 'https://app.pritunl.com/subscription'
        if settings.app.dedicated:
            url = settings.app.dedicated + '/subscription'

        if cancel:
            response = requests.delete(
                url,
                json={
                    'license': settings.app.license,
                },
            )
        else:
            response = requests.put(
                url,
                json={
                    'license': settings.app.license,
                    'card': card,
                    'plan': plan,
                    'email': email,
                },
            )
    except http.client.HTTPException:
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
