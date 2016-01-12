from pritunl import app
from pritunl import logger
from pritunl import utils
from pritunl import auth

@app.app.route('/logs', methods=['GET'])
@auth.session_auth
def logs_get():
    log_view = logger.LogView()
    return utils.jsonify({
        'output': log_view.get_log_lines(
            formatted=False,
            reverse=True,
        ).split('\n'),
    })
