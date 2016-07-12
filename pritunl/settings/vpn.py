from pritunl.settings.group_mongo import SettingsGroupMongo

class SettingsVpn(SettingsGroupMongo):
    group = 'vpn'
    fields = {
        'ipv6': True,
        'ipv6_route_all': True,
        'call_queue_threads': 32,
        'client_ttl': 300,
        'peer_limit': 300,
        'peer_limit_timeout': 10,
        'default_dh_param_bits': 1536,
        'cache_otp_codes': True,
        'log_lines': 5000,
        'server_ping': 10,
        'server_ping_ttl': 30,
        'route_ping': 10,
        'route_ping_ttl': 30,
        'status_update_rate': 3,
        'http_request_timeout': 10,
        'op_timeout': 10,
        'iptables_update': True,
        'iptables_update_rate': 900,
        'bandwidth_update_rate': 15,
        'nat_routes': True,
        'ipv6_prefix': 'fd00',
        'stress_test': False,
        'vxlan_id_start': 9700,
        'vxlan_net_prefix': '100.97.',
        'safe_priv_subnets': [
            '10.0.0.0/8',
            '100.64.0.0/10',
            '172.16.0.0/12',
            '192.0.0.0/24',
            '192.168.0.0/16',
            '198.18.0.0/15',
            '50.203.0.0/16',
        ],
    }
