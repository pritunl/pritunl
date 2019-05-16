from pritunl.constants import *

from pritunl import app
from pritunl import logger
from pritunl import utils
from pritunl import auth
from pritunl import settings

@app.app.route('/logs', methods=['GET'])
@auth.session_auth
def logs_get():
    if settings.app.demo_mode:
        return utils.jsonify({
            'output': DEMO_LOGS,
        })

    log_view = logger.LogView()
    return utils.jsonify({
        'output': log_view.get_log_lines(
            natural=True,
            formatted=False,
            reverse=True,
        ).split('\n'),
    })
