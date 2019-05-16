from pritunl import settings
from pritunl import plugins

def plugin_sso_authenticate(sso_type, user_name, user_email, remote_ip,
        sso_org_names=None, sso_group_names=None):
    from pritunl import organization

    returns = plugins.caller(
        'sso_authenticate',
        sso_type=sso_type,
        host_id=settings.local.host_id,
        host_name=settings.local.host.name,
        user_name=user_name,
        user_email=user_email,
        remote_ip=remote_ip,
        sso_org_names=sso_org_names or [],
        sso_group_names=sso_group_names or [],
    )

    if not returns:
        return True, None, None

    groups = set()
    org_name = None
    for return_val in returns:
        if not return_val[0]:
            return False, None, None
        if return_val[1]:
            org_name = return_val[1]

        if len(return_val) > 2:
            for val in return_val[2]:
                groups.add(val)

    org_id = None
    if org_name:
        org = organization.get_by_name(org_name, fields=('_id'))
        if org:
            org_id = org.id

    return True, org_id, groups or None

def plugin_login_authenticate(user_name, password, remote_ip):
    from pritunl import organization

    returns = plugins.caller(
        'user_authenticate',
        host_id=settings.local.host_id,
        host_name=settings.local.host.name,
        user_name=user_name,
        password=password,
        remote_ip=remote_ip,
    )

    if not returns:
        return False, False, None, None

    org_name = None
    groups = set()
    for return_val in returns:
        if not return_val[0]:
            return True, False, None, None
        if return_val[1]:
            org_name = return_val[1]

        if len(return_val) > 2:
            for val in return_val[2]:
                groups.add(val)

    org_id = None
    if org_name:
        org = organization.get_by_name(org_name, fields=('_id'))
        if org:
            org_id = org.id

    return True, True, org_id, groups or None
