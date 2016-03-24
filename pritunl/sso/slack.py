from pritunl import settings

def verify_slack(username, user_team, user_groups):
    valid = user_team == settings.app.sso_match[0]
    org_name = None
    return valid, org_name
