# Aviaible libraries
# import requests
# import pymongo
# import redis
# import boto

# Called after user has connected.
def user_connected(host_id, server_id, org_id, user_id, host_name,
        server_name, org_name, user_name, platform, device_id, device_name,
        virtual_ip, virtual_ip6, remote_ip, mac_addr, **kwargs):
    pass

# Called on user disconnect, may not always be called if a server is stopped
# or unexpected failure occurs.
def user_disconnected(host_id, server_id, org_id, user_id, host_name,
        server_name, org_name, user_name, remote_ip, **kwargs):
    pass

# [SYNCHRONOUS] Called on user authentication must return True or False
# and None or a string with reason if False.
def user_connect(host_id, server_id, org_id, user_id, host_name,
        server_name, org_name, user_name, remote_ip, platform, device_name,
        password, **kwargs):
    if 'auth_ok':
        return True, None
    else:
        return False, 'Reason for denial'

# [SYNCHRONOUS] Called on user login must return True or False
# and an organization name that the user will be added to. The organization
# name must be included. Also called on each user connection. This plugin is
# used to support user logins with credentials from other systems. The
# user_name and password must be verified in the plugin, no other
# authentication will be checked.
def user_authenticate(host_id, host_name, user_name, password, remote_ip, **kwargs):
    if 'auth_ok':
        return True, 'organization_name'
    else:
        return False, None

# [SYNCHRONOUS] Called after a user has authenticated with SSO when
# loging into the web console. Must return True or False to accept auth
# request and an organization name or None. If an organization name is
# included the user will be added to that organization. If Duo is used as a
# secondary authentication method and the organization name from Duo is set it
# will have priority over the organization name from the primary SSO provider.
def sso_authenticate(sso_type, host_id, host_name, user_name, user_email,
        remote_ip, **kwargs):
    if sso_type == 'duo':
        pass
    elif sso_type == 'google':
        pass
    elif sso_type == 'slack':
        pass
    elif sso_type == 'saml':
        pass
    elif sso_type == 'radius':
        pass

    if 'auth_ok':
        return True, 'organization_name'
    else:
        return False, None
