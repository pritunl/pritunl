from pritunl.constants import *
from pritunl import utils
from pritunl import logger
from pritunl.app_server import app_server

@app_server.app.route('/log', methods=['GET'])
@app_server.auth
def log_get():
    log_entries = []

    for log_entry in logger.iter_log_entries():
        log_entries.append(log_entry.dict())

    return utils.jsonify(log_entries)
