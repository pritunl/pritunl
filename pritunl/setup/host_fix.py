from pritunl import settings

def setup_host_fix():
    if settings.app.license and settings.app.license_plan != 'premium':
        return

    from pritunl import server
    host_id = settings.local.host.id

    for svr in server.iter_servers(fields=['hosts']):
        if svr.hosts != [host_id]:
            svr.hosts = [host_id]
            svr.commit('hosts')
