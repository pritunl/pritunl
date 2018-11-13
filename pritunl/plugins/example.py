# Available libraries included with a default Pritunl installation
from pritunl import logger
# import requests
# import pymongo
# import redis
# import boto3

# Called on authorization of user connection attempt. Allow will be True
# when user authenticated sucessfully. When allow is False reason will
# explain why the user was not authenticated.
def user_connection(host_id, server_id, org_id, user_id, host_name,
        server_name, org_name, user_name, platform, device_id, device_name,
        remote_ip, mac_addr, password, auth_password, auth_token, auth_nonce,
        auth_timestamp, allow, reason, **kwargs):
    logger.info('Example log message', 'plugin',
        key1='value1',
        key2='value2',
    )

    try:
        raise Exception('example')
    except:
        logger.exception('Example exception log message', 'plugin',
            key1='value1',
            key2='value2',
        )

# Called after user has connected.
def user_connected(host_id, server_id, org_id, user_id, host_name,
        server_name, org_name, user_name, platform, device_id, device_name,
        virtual_ip, virtual_ip6, remote_ip, mac_addr, **kwargs):
    pass

# Called on user disconnect, may not always be called if a server is stopped
# or unexpected failure occurs.
def user_disconnected(host_id, server_id, org_id, user_id, host_name,
        server_name, org_name, user_name, remote_ip, virtual_ip, virtual_ip6,
        **kwargs):
    pass

# [SYNCHRONOUS] Called on user connect must return True or False to allow
# connection and None if allowed or a string with reason if not allowed.
def user_connect(host_id, server_id, org_id, user_id, host_name,
        server_name, org_name, user_name, remote_ip, platform, device_name,
        password, **kwargs):
    if not 'auth_ok':
        return True, None
    else:
        return False, 'Reason for denial'

# [SYNCHRONOUS] Called on user login must return True or False and an
# organization name that the user will be added to. The organization name must
# be included. Also called on each user connection. This plugin is used to
# support user logins with credentials from other systems. The user_name and
# password must be verified in the plugin, no other authentication will be
# checked.
def user_authenticate(host_id, host_name, user_name, password, remote_ip,
        **kwargs):
    if not 'auth_ok':
        return True, 'organization_name', ['group', 'names']
    else:
        return False, None, None

# [SYNCHRONOUS] Called when a user configuration is synced or downloaded
# to return custom configuration lines that will be added to the users
# OpenVPN configuration.
def user_config(host_id, host_name, org_id, user_id, user_name, server_id,
        server_name, server_port, server_protocol, server_ipv6,
        server_ipv6_firewall, server_network, server_network6,
        server_network_mode, server_network_start, server_network_stop,
        server_restrict_routes, server_bind_address, server_onc_hostname,
        server_dh_param_bits, server_multi_device, server_dns_servers,
        server_search_domain, server_otp_auth, server_cipher, server_hash,
        server_inter_client, server_ping_interval, server_ping_timeout,
        server_link_ping_interval, server_link_ping_timeout,
        server_allowed_devices, server_max_clients, server_replica_count,
        server_dns_mapping, server_debug, **kwargs):
    return ''

# Called on log entries. The kwargs includes variables from the log event.
def log_entry(host_id, host_name, message, **kwargs):
    pass

# Called on audit event. User id can be referring to a user or administrator.
# The org_id will be None for administrators.
def audit_event(host_id, host_name, user_id, org_id, timestamp, type,
        remote_addr, message, **kwargs):
    pass

# [SYNCHRONOUS] Called after a user has authenticated with SSO when
# loging into the web console. Must return True or False to accept auth
# request and an organization name or None. If an organization name is
# included the user will be added to that organization. If Duo is used as a
# secondary authentication method and the organization name from Duo is set it
# will have priority over the organization name from the primary SSO provider.
# The sso_org_names will specify the list of org names provided by SAML and
# Slack single sign-on.
def sso_authenticate(sso_type, host_id, host_name, user_name, user_email,
        remote_ip, sso_org_names, sso_group_names, **kwargs):
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

    if not 'auth_ok':
        return True, 'organization_name', ['group', 'names']
    else:
        return False, None, None

# [SYNCHRONOUS] Called when a server is started to return custom configuration
# lines that will be added to the servers OpenVPN configuration.
def server_config(host_id, host_name, server_id, server_name, port, protocol,
        ipv6, ipv6_firewall, network, network6, network_mode, network_start,
        network_stop, restrict_routes, bind_address, onc_hostname,
        dh_param_bits, multi_device, dns_servers, search_domain, otp_auth,
        cipher, hash, inter_client, ping_interval, ping_timeout,
        link_ping_interval, link_ping_timeout, max_clients, replica_count,
        dns_mapping, debug, routes, interface, bridge_interface, vxlan,
        **kwargs):
    return ''

# [SYNCHRONOUS] Called when a server is started. Call occurs after OpenVPN
# process has been configured and started.
def server_start(host_id, host_name, server_id, server_name, port, protocol,
        ipv6, ipv6_firewall, network, network6, network_mode, network_start,
        network_stop, restrict_routes, bind_address, onc_hostname,
        dh_param_bits, multi_device, dns_servers, search_domain, otp_auth,
        cipher, hash, inter_client, ping_interval, ping_timeout,
        link_ping_interval, link_ping_timeout, max_clients, replica_count,
        dns_mapping, debug, interface, bridge_interface, vxlan, **kwargs):
    pass

# [SYNCHRONOUS] Called when a server is stopped.
def server_stop(host_id, host_name, server_id, server_name, port, protocol,
        ipv6, ipv6_firewall, network, network6, network_mode, network_start,
        network_stop, restrict_routes, bind_address, onc_hostname,
        dh_param_bits, multi_device, dns_servers, search_domain, otp_auth,
        cipher, hash, inter_client, ping_interval, ping_timeout,
        link_ping_interval, link_ping_timeout, max_clients, replica_count,
        dns_mapping, debug, interface, bridge_interface, vxlan, **kwargs):
    pass
