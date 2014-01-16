from pritunl.constants import *
from pritunl.log_entry import LogEntry
import pritunl.utils as utils
from pritunl import app_server

@app_server.app.route('/log', methods=['GET'])
@app_server.auth
def log_get():
    log_entries = []

    for log_entry in LogEntry.get_log_entries():
        print log_entry.time
        log_entries.append({
            'id': log_entry.id,
            'time': log_entry.time,
            'message': log_entry.message,
        })

    return utils.jsonify(log_entries)
