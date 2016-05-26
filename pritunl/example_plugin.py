# Aviaible libraries
import requests
import pymongo
import redis
import boto

# Called on user connect.
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
def user_authenticate(host_id, server_id, org_id, user_id, host_name,
        server_name, org_name, user_name, remote_ip, platform, device_name,
        password, **kwargs):
    if 'auth_ok':
        return True, None
    else:
        return False, 'Reason for denial'
