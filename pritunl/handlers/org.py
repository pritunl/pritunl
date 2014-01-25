from pritunl.constants import *
from pritunl.organization import Organization
import pritunl.utils as utils
from pritunl import app_server
import flask

@app_server.app.route('/organization', methods=['GET'])
@app_server.auth
def org_get():
    orgs = []

    for org in Organization.iter_orgs():
        orgs.append(org.dict())

    return utils.jsonify(orgs)

@app_server.app.route('/organization', methods=['POST'])
@app_server.auth
def org_post():
    name = flask.request.json['name']
    name = ''.join(x for x in name if x.isalnum() or x in NAME_SAFE_CHARS)
    org = Organization(name=name)
    return utils.jsonify(org.dict())

@app_server.app.route('/organization/<org_id>', methods=['PUT'])
@app_server.auth
def org_put(org_id):
    org = Organization.get_org(id=org_id)
    name = flask.request.json['name']
    name = ''.join(x for x in name if x.isalnum() or x in NAME_SAFE_CHARS)
    org.rename(name)
    return utils.jsonify(org.dict())

@app_server.app.route('/organization/<org_id>', methods=['DELETE'])
@app_server.auth
def org_delete(org_id):
    org = Organization.get_org(id=org_id)
    org.remove()
    return utils.jsonify({})
