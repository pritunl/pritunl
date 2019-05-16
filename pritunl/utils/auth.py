from pritunl import settings

def get_onelogin_mode():
    if settings.app.sso_onelogin_mode is not None:
        return settings.app.sso_onelogin_mode
    if settings.app.sso_onelogin_push:
        if settings.app.sso_onelogin_skip_unavailable:
            return 'push_none'
        return 'push'
    return ''

def get_okta_mode():
    if settings.app.sso_okta_mode is not None:
        return settings.app.sso_okta_mode
    if settings.app.sso_okta_push:
        if settings.app.sso_okta_skip_unavailable:
            return 'push_none'
        return 'push'
    return ''
