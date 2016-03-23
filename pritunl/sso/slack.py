from pritunl import settings

def verify_slack(username, user_team, user_groups):
    return user_team == settings.app.sso_match[0], None
