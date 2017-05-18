from pritunl import settings

def verify_google(user_email):
    user_domain = user_email.split('@')[-1]
    match = False
    for d in settings.app.sso_match:
        if d == user_domain: match = True
    return match
