from pritunl import settings

def get_onelogin_mode():
    if settings.app.sso_onelogin_mode is not None:
        print 'onelogin_%s' % settings.app.sso_onelogin_mode
        return settings.app.sso_onelogin_mode
    if settings.app.sso_onelogin_push:
        if settings.app.sso_onelogin_skip_unavailable:
            print 'onelogin_push_none'
            return 'push_none'
        print 'onelogin_push'
        return 'push'
    print 'onelogin_none'
    return ''

def get_okta_mode():
    if settings.app.sso_okta_mode is not None:
        print 'okta_%s' % settings.app.sso_onelogin_mode
        return settings.app.sso_okta_mode
    if settings.app.sso_okta_push:
        if settings.app.sso_okta_skip_unavailable:
            print 'okta_push_none'
            return 'push_none'
        print 'okta_push'
        return 'push'
    print 'okta_none'
    return ''
