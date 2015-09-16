from pritunl import settings

def upgrade_1_5():
    if settings.app.sso:
        settings.app.sso = 'google'
    elif settings.app.sso is not None:
        settings.app.sso = None
    else:
        return
    settings.commit()
