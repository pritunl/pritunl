from pritunl import settings

def verify_google(user_email):
    user_domain = user_email.split('@')[-1]
    valid = user_domain in settings.app.sso_match
    org_name = None
    return valid, org_name
