from pritunl.constants import *
from pritunl.organization import Organization
import pritunl.utils as utils
from pritunl import app_server
import flask

@app_server.app.route('/organization', methods=['GET'])
@app_server.app.route('/organization/<org_id>', methods=['GET'])
@app_server.auth
def org_get(org_id=None):
    if org_id:
        return utils.jsonify(Organization.get_org(id=org_id).dict())
    else:
        orgs = []
        for org in Organization.iter_orgs():
            orgs.append(org.dict())
        return utils.jsonify(orgs)

@app_server.app.route('/organization', methods=['POST'])
@app_server.auth
def org_post():
    name = utils.filter_str(flask.request.json['name'])
    org = Organization(name=name)
    return utils.jsonify(org.dict())

@app_server.app.route('/organization/<org_id>', methods=['PUT'])
@app_server.auth
def org_put(org_id):
    org = Organization.get_org(id=org_id)
    name = utils.filter_str(flask.request.json['name'])
    org.rename(name)
    return utils.jsonify(org.dict())

@app_server.app.route('/organization/<org_id>', methods=['DELETE'])
@app_server.auth
def org_delete(org_id):
    org = Organization.get_org(id=org_id)
    org.remove()
    return utils.jsonify({})
