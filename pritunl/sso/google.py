from pritunl import settings

def verify_google(user_email):
    user_domain = user_email.split('@')[-1]
    return user_domain in settings.app.sso_match
