from pritunl.constants import *
from pritunl.organization import Organization
import pritunl.utils as utils
from pritunl import server
import flask

@server.app.route('/organization', methods=['GET'])
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

@server.app.route('/organization', methods=['POST'])
def org_post():
    name = flask.request.json['name'].encode()
    org = Organization(name=name)

    return utils.jsonify({
        'id': org.id,
        'name': org.name,
    })

@server.app.route('/organization/<org_id>', methods=['PUT'])
def org_put(org_id):
    org = Organization(org_id)
    org.rename(flask.request.json['name'].encode())
    return utils.jsonify({})

@server.app.route('/organization/<org_id>', methods=['DELETE'])
def org_delete(org_id):
    org = Organization(org_id)
    org.remove()
    return utils.jsonify({})
