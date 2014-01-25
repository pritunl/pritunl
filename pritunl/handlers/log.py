from pritunl.constants import *
from pritunl.log_entry import LogEntry
import pritunl.utils as utils
from pritunl import app_server

@app_server.app.route('/log', methods=['GET'])
@app_server.auth
def log_get():
    log_entries = []

    for log_entry in LogEntry.iter_log_entries():
        log_entries.append(log_entry.dict())

    return utils.jsonify(log_entries)
