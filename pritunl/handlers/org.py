from pritunl.constants import *
from pritunl.organization import Organization
import pritunl.utils as utils
from pritunl import app_server
import flask

@app_server.app.route('/organization', methods=['GET'])
@app_server.auth
def org_get():
    orgs = []
    orgs_dict = {}
    orgs_sort = []

    for org in Organization.get_orgs():
        name_id = '%s_%s' % (org.name, org.id)
        orgs_sort.append(name_id)
        orgs_dict[name_id] = {
            'id': org.id,
            'name': org.name,
        }

    for name_id in sorted(orgs_sort):
        orgs.append(orgs_dict[name_id])

    return utils.jsonify(orgs)

@app_server.app.route('/organization', methods=['POST'])
@app_server.auth
def org_post():
    name = flask.request.json['name']
    name = ''.join(x for x in name if x.isalnum() or x in NAME_SAFE_CHARS)
    org = Organization(name=name)
    return utils.jsonify({})

@app_server.app.route('/organization/<org_id>', methods=['PUT'])
@app_server.auth
def org_put(org_id):
    org = Organization(org_id)
    name = flask.request.json['name']
    name = ''.join(x for x in name if x.isalnum() or x in NAME_SAFE_CHARS)
    org.rename(name)
    return utils.jsonify({})

@app_server.app.route('/organization/<org_id>', methods=['DELETE'])
@app_server.auth
def org_delete(org_id):
    org = Organization(org_id)
    org.remove()
    return utils.jsonify({})
