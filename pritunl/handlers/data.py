from pritunl.constants import *
from pritunl.organization import Organization
from pritunl.server import Server
import pritunl.utils as utils
from pritunl import app_server
import os
import flask
import tarfile
import time

def tar_add(tar_file, path):
    if os.path.exists(path):
        tar_file.add(path, arcname=os.path.relpath(path, app_server.data_path))

@app_server.app.route('/export', methods=['GET'])
@app_server.app.route('/export/%s.tar' % APP_NAME, methods=['GET'])
@app_server.auth
def export_get():
    data_path = app_server.data_path
    temp_path = os.path.join(data_path, TEMP_DIR)
    empty_temp_path = os.path.join(temp_path, EMPTY_TEMP_DIR)
    data_archive_name = '%s_%s.tar' % (APP_NAME,
        time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime()))
    data_archive_path = os.path.join(temp_path, data_archive_name)

    # Create empty temp directory to recreate temp dirs in tarfile
    if not os.path.exists(empty_temp_path):
        os.makedirs(empty_temp_path)

    tar_file = tarfile.open(data_archive_path, 'w')
    try:
        tar_add(tar_file, os.path.join(data_path, SERVER_CERT_NAME))
        tar_add(tar_file, os.path.join(data_path, SERVER_KEY_NAME))
        tar_add(tar_file, os.path.join(data_path, VERSION_NAME))

        for org in Organization.get_orgs():
            tar_add(tar_file, org.index_path)
            tar_add(tar_file, org.index_attr_path)
            tar_add(tar_file, org.serial_path)
            tar_add(tar_file, org.crl_path)
            tar_add(tar_file, org.get_path())
            print os.path.relpath(os.path.join(org.path, TEMP_DIR),
                    data_path)
            tar_file.add(empty_temp_path,
                arcname=os.path.relpath(os.path.join(org.path, TEMP_DIR),
                    data_path))

            indexed_certs_path = os.path.join(org.path, INDEXED_CERTS_DIR)
            for path in os.listdir(indexed_certs_path):
                tar_add(tar_file, os.path.join(indexed_certs_path, path))

            for user in org.get_users() + [org.ca_cert]:
                tar_add(tar_file, user.reqs_path)
                tar_add(tar_file, user.ssl_conf_path)
                tar_add(tar_file, user.key_path)
                tar_add(tar_file, user.cert_path)
                tar_add(tar_file, user.key_archive_path)
                tar_add(tar_file, user.get_path())

        for server in Server.get_servers():
            tar_add(tar_file, server.dh_param_path)
            tar_add(tar_file, server.ifc_pool_path)
            tar_add(tar_file, server.get_path())
            tar_file.add(empty_temp_path,
                arcname=os.path.relpath(os.path.join(server.path, TEMP_DIR),
                    data_path))
    finally:
        tar_file.close()

    with open(data_archive_path, 'r') as archive_file:
        response = flask.Response(response=archive_file.read(),
            mimetype='application/x-tar')
        response.headers.add('Content-Disposition',
            'inline; filename="%s.tar"' % data_archive_name)

    os.remove(data_archive_path)
    return response
