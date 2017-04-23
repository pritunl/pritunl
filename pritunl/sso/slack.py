from pritunl import settings

def verify_slack(username, user_team):
    valid = user_team == settings.app.sso_match[0]
    return valid
