from pritunl import radius
from pritunl import settings

def verify_radius(username, password):
    host = settings.app.sso_host.split(':')
    if len(host) > 1:
        port = int(host[1])
    else:
        port = 1645
    host = host[0]

    resp = radius.authenticate(
        (settings.app.sso_radius_prefix or '') + username.encode(),
        password.encode(),
        settings.app.sso_secret.encode(),
        host=host,
        port=port,
    )

    return resp == 1, None
