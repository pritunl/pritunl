from pritunl.constants import *
import pritunl.utils as utils
from pritunl import app_server
from pritunl.cache import persist_db
import flask
import re

@app_server.app.route('/subscription', methods=['GET'])
@app_server.auth
def subscription_get():
    app_server.subscription_update()
    return utils.jsonify(app_server.subscription_dict())

@app_server.app.route('/subscription/state', methods=['GET'])
def subscription_state_get():
    app_server.subscription_update()
    return utils.jsonify({
        'active': app_server.sub_active,
    })

@app_server.app.route('/subscription', methods=['POST'])
@app_server.auth
def subscription_post():
    license = flask.request.json['license']
    license = license.lower().replace('begin license', '').replace(
        'end license', '')
    license = re.sub(r'[\W_]+', '', license)

    try:
        response = utils.request.get(SUBSCRIPTION_SERVER,
            json_data={'license': license})
    except httplib.HTTPException:
        return utils.jsonify({
            'error': SUBSCRIPTION_SERVER_ERROR,
            'error_msg': SUBSCRIPTION_SERVER_ERROR_MSG,
        }, 500)
    data = response.json()

    if response.status_code != 200:
        return utils.jsonify(data, response.status_code);

    persist_db.set('license', license)
    app_server.subscription_update()
    return utils.jsonify(app_server.subscription_dict())

@app_server.app.route('/subscription', methods=['PUT'])
@app_server.auth
def subscription_put():
    card = flask.request.json.get('card')
    email = flask.request.json.get('email')
    cancel = flask.request.json.get('cancel')

    try:
        if cancel:
            response = utils.request.delete(SUBSCRIPTION_SERVER,
                json_data={
                    'license': persist_db.get('license'),
                },
            )
        else:
            response = utils.request.put(SUBSCRIPTION_SERVER,
                json_data={
                    'license': persist_db.get('license'),
                    'card': card,
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

    app_server.subscription_update()
    return utils.jsonify(app_server.subscription_dict())

@app_server.app.route('/subscription', methods=['DELETE'])
@app_server.auth
def subscription_delete():
    persist_db.remove('license')
    app_server.subscription_update()
    return utils.jsonify({})
