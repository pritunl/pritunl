from pritunl.constants import *
from pritunl import settings
from pritunl import logger
from pritunl.pyrad import client
from pritunl.pyrad import packet
from pritunl.pyrad import dictionary

import io

def verify_radius(username, password):
    hosts = settings.app.sso_radius_host.split(',')

    for i, host in enumerate(hosts):
        host = host.split(':')
        if len(host) > 1:
            port = int(host[1])
        else:
            port = 1645
        host = host[0]

        conn = client.Client(
            server=host,
            authport=port,
            secret=settings.app.sso_radius_secret.encode(),
            dict=dictionary.Dictionary(
                io.StringIO(RADIUS_DICTONARY)),
        )

        if settings.app.sso_radius_timeout:
            conn.timeout = settings.app.sso_radius_timeout

        req = conn.CreateAuthPacket(
            code=packet.AccessRequest,
            User_Name=(
                settings.app.sso_radius_prefix or '') + username.encode(),
        )
        req['User-Password'] = req.PwCrypt(password)

        try:
            reply = conn.SendPacket(req)
        except:
            if i == len(hosts) - 1:
                raise
            else:
                continue

        if reply.code != packet.AccessAccept:
            if i == len(hosts) - 1:
                logger.warning('Radius server rejected authentication', 'sso',
                    username=username,
                    reply_code=reply.code,
                )
                return False, None, None
            else:
                continue

        break

    org_names = []
    try:
        org_names = reply.get((97, 0)) or []
    except:
        pass

    group_names = []
    try:
        group_names = reply.get((97, 1)) or []
    except:
        pass

    org_names2 = []
    try:
        org_names2 = reply.get(97) or []
    except:
        pass

    org_names = org_names or org_names2

    groups = set()
    for group in group_names:
        groups.add(group)

    return True, org_names, groups
