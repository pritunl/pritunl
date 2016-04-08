from pritunl.constants import *
from pritunl import logger
from pritunl import utils
from pritunl import event
from pritunl import organization
from pritunl import app
from pritunl import auth
from pritunl import settings

import flask

@app.app.route('/organization', methods=['GET'])
@app.app.route('/organization/<org_id>', methods=['GET'])
@auth.session_auth
def org_get(org_id=None):
    if org_id:
        if settings.app.demo_mode:
            resp = utils.demo_get_cache()
            if resp:
                return utils.jsonify(resp)

        resp = organization.get_by_id(org_id).dict()
        if settings.app.demo_mode:
            utils.demo_set_cache(resp)
        return utils.jsonify(resp)

    orgs = []
    page = flask.request.args.get('page', None)
    page = int(page) if page else page

    if settings.app.demo_mode:
        resp = utils.demo_get_cache(page)
        if resp:
            return utils.jsonify(resp)

    for org in organization.iter_orgs(page=page):
        orgs.append(org.dict())

    if page is not None:
        resp = {
            'page': page,
            'page_total': organization.get_org_page_total(),
            'organizations': orgs,
        }
    else:
        resp = orgs

    if settings.app.demo_mode:
        utils.demo_set_cache(resp, page)
    return utils.jsonify(resp)

@app.app.route('/organization', methods=['POST'])
@auth.session_auth
def org_post():
    if settings.app.demo_mode:
        return utils.demo_blocked()

    name = utils.filter_str(flask.request.json['name'])
    auth_api = flask.request.json.get('auth_api', False)

    org = organization.new_org(name=name, auth_api=None, type=ORG_DEFAULT)

    if auth_api:
        org.auth_api = True
        org.generate_auth_token()
        org.generate_auth_secret()
        org.commit()

    logger.LogEntry(message='Created new organization "%s".' % org.name)
    event.Event(type=ORGS_UPDATED)
    return utils.jsonify(org.dict())

@app.app.route('/organization/<org_id>', methods=['PUT'])
@auth.session_auth
def org_put(org_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    org = organization.get_by_id(org_id)

    org.name = utils.filter_str(flask.request.json['name'])

    auth_api = flask.request.json.get('auth_api', False)
    if auth_api:
        org.auth_api = True
        if not org.auth_token:
            org.generate_auth_token()
        if not org.auth_secret:
            org.generate_auth_secret()
    else:
        org.auth_api = False
        org.auth_token = None
        org.auth_secret = None

    if flask.request.json.get('auth_token') == True:
        org.generate_auth_token()

    if flask.request.json.get('auth_secret') == True:
        org.generate_auth_secret()

    org.commit()
    event.Event(type=ORGS_UPDATED)
    return utils.jsonify(org.dict())

@app.app.route('/organization/<org_id>', methods=['DELETE'])
@auth.session_auth
def org_delete(org_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    org = organization.get_by_id(org_id)
    name = org.name
    server_ids = org.remove()

    logger.LogEntry(message='Deleted organization "%s".' % name)

    for server_id in server_ids:
        event.Event(type=SERVER_ORGS_UPDATED, resource_id=server_id)
    event.Event(type=SERVERS_UPDATED)
    event.Event(type=ORGS_UPDATED)

    return utils.jsonify({})
