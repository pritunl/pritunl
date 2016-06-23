from pritunl.constants import *
from pritunl import settings
from pritunl.pyrad import client
from pritunl.pyrad import packet
from pritunl.pyrad import dictionary

import StringIO

def verify_radius(username, password):
    host = settings.app.sso_host.split(':')
    if len(host) > 1:
        port = int(host[1])
    else:
        port = 1645
    host = host[0]

    conn = client.Client(
        server=host,
        authport=port,
        secret=settings.app.sso_secret.encode(),
        dict=dictionary.Dictionary(StringIO.StringIO(RADIUS_DICTONARY)),
    )

    req = conn.CreateAuthPacket(
        code=packet.AccessRequest,
        User_Name=(settings.app.sso_radius_prefix or '') + username.encode(),
    )
    req['User-Password'] = req.PwCrypt(password.encode())

    reply = conn.SendPacket(req)

    if reply.code != packet.AccessAccept:
        return False, None, None

    org_names = reply.get((97, 0)) or []
    groups = set()
    for group in reply.get((97, 1)) or []:
        groups.add(group)

    return True, org_names, groups
