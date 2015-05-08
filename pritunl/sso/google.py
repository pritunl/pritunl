from pritunl import settings

def verify_google(user_email, org_id):
    user_domain = user_email.split('@')[-1]
    return user_domain in settings.app.sso_match, org_id
