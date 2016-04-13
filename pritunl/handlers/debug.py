from pritunl import auth
from pritunl import app

@app.app.route('/debug/restart_web', methods=['GET'])
@auth.session_auth
def restart_web_get():
    app.restart_server(1)
    return 'restarting web server...'
