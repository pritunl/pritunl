import string

APP_NAME = 'pritunl'
APP_NAME_FORMATED = 'Pritunl'
CONF_FILENAME = '%s.conf' % APP_NAME
MIN_DATABASE_VER = '1.25.0.0'
SE_MODE = False

SAVED = 'saved'
UNSAVED = 'unsaved'

START = 'start'
STOP = 'stop'
RESTART = 'restart'

RUNNING = 'running'
PAUSED = 'paused'
STOPPED = 'stopped'

PENDING = 'pending'
COMMITTED = 'committed'
ROLLBACK = 'rollback'
COMPLETE = 'complete'
UPDATE = 'update'

ONLINE = 'online'
OFFLINE = 'offline'

AVAILABLE = 'available'
UNAVAILABLE = 'unavailable'
ACTIVE_UNAVAILABLE = 'active_unavailable'
ACTIVE = 'active'

CONNECTED = 'connected'
DISCONNECTED = 'disconnected'

DEFAULT = 'default'

TUNNEL = 'tunnel'
BRIDGE = 'bridge'

PIN_REQUIRED = 'required'
PIN_OPTIONAL = 'optional'
PIN_DISABLED = 'disabled'

SITE_TO_SITE = 'site_to_site'
DIRECT = 'direct'
DIRECT_SERVER = 'direct_server'
DIRECT_CLIENT = 'direct_client'

HOLD = 'hold'

VERY_LOW = 0
LOW = 1
NORMAL = 2
HIGH = 3
VERY_HIGH = 4

LOW_CPU = 0
NORMAL_CPU = 1
HIGH_CPU = 2

BULK_EXECUTE = 'bulk_execute'

MONGO_ACTION_METHODS = {
    'update',
    'remove',
    'find',
    'find_one',
    'find_and_modify',
    'replace_one',
    'update_one',
    'remove_one',
    'upsert',
}

AWS_REGIONS = {
    'us-east-1',
    'us-east-2',
    'us-west-1',
    'us-west-2',
    'us-gov-east-1',
    'us-gov-west-1',
    'eu-north-1',
    'eu-west-1',
    'eu-west-2',
    'eu-west-3',
    'eu-central-1',
    'ca-central-1',
    'cn-north-1',
    'cn-northwest-1',
    'ap-northeast-1',
    'ap-northeast-2',
    'ap-southeast-1',
    'ap-southeast-2',
    'ap-east-1',
    'ap-south-1',
    'sa-east-1',
}

OK = 'ok'
DISABLED = 'disabled'

NAME_SAFE_CHARS = {
    '-', '=', '_', '@', '.', ':', '/',
    '!', '#', '$', '%', '&', '*', '+',
    '?', '^', '`', '{', '|', '}', '~',
}

VALID_CHARS = {
    'a', 'b', 'c', 'd', 'e', 'f', 'g',
    'h', 'i', 'j', 'k', 'l', 'm', 'n',
    'o', 'p', 'q', 'r', 's', 't', 'u',
    'v', 'w', 'x', 'y', 'z', 'A', 'B',
    'C', 'D', 'E', 'F', 'G', 'H', 'I',
    'J', 'K', 'L', 'M', 'N', 'O', 'P',
    'Q', 'R', 'S', 'T', 'U', 'V', 'W',
    'X', 'Y', 'Z', '0', '1', '2', '3',
    '4', '5', '6', '7', '8', '9', '=',
}

INVALID_NAMES = {
    'nil',
    'null',
    'none',
    'undefined',
    'empty',
    'true',
    'false',
    '1',
    '0',
    'blocked',
    'disabled',
    'invalid',
    'inactive',
    'error',
}

LETS_ENCRYPT_INTER = """
-----BEGIN CERTIFICATE-----
MIIFFjCCAv6gAwIBAgIRAJErCErPDBinU/bWLiWnX1owDQYJKoZIhvcNAQELBQAw
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMjAwOTA0MDAwMDAw
WhcNMjUwOTE1MTYwMDAwWjAyMQswCQYDVQQGEwJVUzEWMBQGA1UEChMNTGV0J3Mg
RW5jcnlwdDELMAkGA1UEAxMCUjMwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEK
AoIBAQC7AhUozPaglNMPEuyNVZLD+ILxmaZ6QoinXSaqtSu5xUyxr45r+XXIo9cP
R5QUVTVXjJ6oojkZ9YI8QqlObvU7wy7bjcCwXPNZOOftz2nwWgsbvsCUJCWH+jdx
sxPnHKzhm+/b5DtFUkWWqcFTzjTIUu61ru2P3mBw4qVUq7ZtDpelQDRrK9O8Zutm
NHz6a4uPVymZ+DAXXbpyb/uBxa3Shlg9F8fnCbvxK/eG3MHacV3URuPMrSXBiLxg
Z3Vms/EY96Jc5lP/Ooi2R6X/ExjqmAl3P51T+c8B5fWmcBcUr2Ok/5mzk53cU6cG
/kiFHaFpriV1uxPMUgP17VGhi9sVAgMBAAGjggEIMIIBBDAOBgNVHQ8BAf8EBAMC
AYYwHQYDVR0lBBYwFAYIKwYBBQUHAwIGCCsGAQUFBwMBMBIGA1UdEwEB/wQIMAYB
Af8CAQAwHQYDVR0OBBYEFBQusxe3WFbLrlAJQOYfr52LFMLGMB8GA1UdIwQYMBaA
FHm0WeZ7tuXkAXOACIjIGlj26ZtuMDIGCCsGAQUFBwEBBCYwJDAiBggrBgEFBQcw
AoYWaHR0cDovL3gxLmkubGVuY3Iub3JnLzAnBgNVHR8EIDAeMBygGqAYhhZodHRw
Oi8veDEuYy5sZW5jci5vcmcvMCIGA1UdIAQbMBkwCAYGZ4EMAQIBMA0GCysGAQQB
gt8TAQEBMA0GCSqGSIb3DQEBCwUAA4ICAQCFyk5HPqP3hUSFvNVneLKYY611TR6W
PTNlclQtgaDqw+34IL9fzLdwALduO/ZelN7kIJ+m74uyA+eitRY8kc607TkC53wl
ikfmZW4/RvTZ8M6UK+5UzhK8jCdLuMGYL6KvzXGRSgi3yLgjewQtCPkIVz6D2QQz
CkcheAmCJ8MqyJu5zlzyZMjAvnnAT45tRAxekrsu94sQ4egdRCnbWSDtY7kh+BIm
lJNXoB1lBMEKIq4QDUOXoRgffuDghje1WrG9ML+Hbisq/yFOGwXD9RiX8F6sw6W4
avAuvDszue5L3sz85K+EC4Y/wFVDNvZo4TYXao6Z0f+lQKc0t8DQYzk1OXVu8rp2
yJMC6alLbBfODALZvYH7n7do1AZls4I9d1P4jnkDrQoxB3UqQ9hVl3LEKQ73xF1O
yK5GhDDX8oVfGKF5u+decIsH4YaTw7mP3GFxJSqv3+0lUFJoi5Lc5da149p90Ids
hCExroL1+7mryIkXPeFM5TgO9r0rvZaBFOvV2z0gp35Z0+L4WPlbuEjN/lxPFin+
HlUjr8gRsI3qfJOQFy/9rKIJR0Y/8Omwt/8oTWgy1mdeHmmjk7j1nYsvC9JSQ6Zv
MldlTTKB3zhThV1+XWYp6rjd5JW1zbVWEkLNxE7GJThEUG3szgBVGP7pSWTUTsqX
nLRbwHOoq7hHwg==
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIICxjCCAk2gAwIBAgIRALO93/inhFu86QOgQTWzSkUwCgYIKoZIzj0EAwMwTzEL
MAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2VhcmNo
IEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDIwHhcNMjAwOTA0MDAwMDAwWhcN
MjUwOTE1MTYwMDAwWjAyMQswCQYDVQQGEwJVUzEWMBQGA1UEChMNTGV0J3MgRW5j
cnlwdDELMAkGA1UEAxMCRTEwdjAQBgcqhkjOPQIBBgUrgQQAIgNiAAQkXC2iKv0c
S6Zdl3MnMayyoGli72XoprDwrEuf/xwLcA/TmC9N/A8AmzfwdAVXMpcuBe8qQyWj
+240JxP2T35p0wKZXuskR5LBJJvmsSGPwSSB/GjMH2m6WPUZIvd0xhajggEIMIIB
BDAOBgNVHQ8BAf8EBAMCAYYwHQYDVR0lBBYwFAYIKwYBBQUHAwIGCCsGAQUFBwMB
MBIGA1UdEwEB/wQIMAYBAf8CAQAwHQYDVR0OBBYEFFrz7Sv8NsI3eblSMOpUb89V
yy6sMB8GA1UdIwQYMBaAFHxClq7eS0g7+pL4nozPbYupcjeVMDIGCCsGAQUFBwEB
BCYwJDAiBggrBgEFBQcwAoYWaHR0cDovL3gyLmkubGVuY3Iub3JnLzAnBgNVHR8E
IDAeMBygGqAYhhZodHRwOi8veDIuYy5sZW5jci5vcmcvMCIGA1UdIAQbMBkwCAYG
Z4EMAQIBMA0GCysGAQQBgt8TAQEBMAoGCCqGSM49BAMDA2cAMGQCMHt01VITjWH+
Dbo/AwCd89eYhNlXLr3pD5xcSAQh8suzYHKOl9YST8pE9kLJ03uGqQIwWrGxtO3q
YJkgsTgDyj2gJrjubi1K9sZmHzOa25JK1fUpE8ZwYii6I4zPPS/Lgul/
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIEZTCCA02gAwIBAgIQQAF1BIMUpMghjISpDBbN3zANBgkqhkiG9w0BAQsFADA/
MSQwIgYDVQQKExtEaWdpdGFsIFNpZ25hdHVyZSBUcnVzdCBDby4xFzAVBgNVBAMT
DkRTVCBSb290IENBIFgzMB4XDTIwMTAwNzE5MjE0MFoXDTIxMDkyOTE5MjE0MFow
MjELMAkGA1UEBhMCVVMxFjAUBgNVBAoTDUxldCdzIEVuY3J5cHQxCzAJBgNVBAMT
AlIzMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuwIVKMz2oJTTDxLs
jVWSw/iC8ZmmekKIp10mqrUrucVMsa+Oa/l1yKPXD0eUFFU1V4yeqKI5GfWCPEKp
Tm71O8Mu243AsFzzWTjn7c9p8FoLG77AlCQlh/o3cbMT5xys4Zvv2+Q7RVJFlqnB
U840yFLuta7tj95gcOKlVKu2bQ6XpUA0ayvTvGbrZjR8+muLj1cpmfgwF126cm/7
gcWt0oZYPRfH5wm78Sv3htzB2nFd1EbjzK0lwYi8YGd1ZrPxGPeiXOZT/zqItkel
/xMY6pgJdz+dU/nPAeX1pnAXFK9jpP+Zs5Od3FOnBv5IhR2haa4ldbsTzFID9e1R
oYvbFQIDAQABo4IBaDCCAWQwEgYDVR0TAQH/BAgwBgEB/wIBADAOBgNVHQ8BAf8E
BAMCAYYwSwYIKwYBBQUHAQEEPzA9MDsGCCsGAQUFBzAChi9odHRwOi8vYXBwcy5p
ZGVudHJ1c3QuY29tL3Jvb3RzL2RzdHJvb3RjYXgzLnA3YzAfBgNVHSMEGDAWgBTE
p7Gkeyxx+tvhS5B1/8QVYIWJEDBUBgNVHSAETTBLMAgGBmeBDAECATA/BgsrBgEE
AYLfEwEBATAwMC4GCCsGAQUFBwIBFiJodHRwOi8vY3BzLnJvb3QteDEubGV0c2Vu
Y3J5cHQub3JnMDwGA1UdHwQ1MDMwMaAvoC2GK2h0dHA6Ly9jcmwuaWRlbnRydXN0
LmNvbS9EU1RST09UQ0FYM0NSTC5jcmwwHQYDVR0OBBYEFBQusxe3WFbLrlAJQOYf
r52LFMLGMB0GA1UdJQQWMBQGCCsGAQUFBwMBBggrBgEFBQcDAjANBgkqhkiG9w0B
AQsFAAOCAQEA2UzgyfWEiDcx27sT4rP8i2tiEmxYt0l+PAK3qB8oYevO4C5z70kH
ejWEHx2taPDY/laBL21/WKZuNTYQHHPD5b1tXgHXbnL7KqC401dk5VvCadTQsvd8
S8MXjohyc9z9/G2948kLjmE6Flh9dDYrVYA9x2O+hEPGOaEOa1eePynBgPayvUfL
qjBstzLhWVQLGAkXXmNs+5ZnPBxzDJOLxhF2JIbeQAcH5H0tZrUlo5ZYyOqA7s9p
O5b85o3AM/OJ+CktFBQtfvBhcJVd9wvlwPsk+uyOy2HI7mNxKKgsBTt375teA2Tw
UdHkhVNcsAKX1H7GNNLOEADksd86wuoXvg==
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIEZTCCA02gAwIBAgIQQAF1BIMlO+Rkt3exI9CKgjANBgkqhkiG9w0BAQsFADA/
MSQwIgYDVQQKExtEaWdpdGFsIFNpZ25hdHVyZSBUcnVzdCBDby4xFzAVBgNVBAMT
DkRTVCBSb290IENBIFgzMB4XDTIwMTAwNzE5MjE0NVoXDTIxMDkyOTE5MjE0NVow
MjELMAkGA1UEBhMCVVMxFjAUBgNVBAoTDUxldCdzIEVuY3J5cHQxCzAJBgNVBAMT
AlI0MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsyjcdynT55G+87cK
AMf78lULJSJjUzav6Qgg3w2vKD7NxqtXtp2kJRml0jJtSaYIuccvoZuTxSBAa4Qx
IKKOMGAlYO/ZGok/H2lxstrqP3NBxJBvZv19nljYd8/NWXVEyaEKe58/Gw46Zm+2
dc+Ly6+dwHDF/9KCCq9dzeLonIWUpOYANeh+TjmBxyGJYHfqHZbyi4N7R8RtMsBS
fiMeRbVx7qPvF8IDqZOJ3fWf27rx2uB+l4dxgR4aglbkPnwYogjlFl+o+qjgSFFN
GBSgDKPltsqztVUSa3LHWn87jPnn2dGOEk0zMwMq8RPhQjzCLllgLm3gB0czZd/S
Z8pNhQIDAQABo4IBaDCCAWQwEgYDVR0TAQH/BAgwBgEB/wIBADAOBgNVHQ8BAf8E
BAMCAYYwSwYIKwYBBQUHAQEEPzA9MDsGCCsGAQUFBzAChi9odHRwOi8vYXBwcy5p
ZGVudHJ1c3QuY29tL3Jvb3RzL2RzdHJvb3RjYXgzLnA3YzAfBgNVHSMEGDAWgBTE
p7Gkeyxx+tvhS5B1/8QVYIWJEDBUBgNVHSAETTBLMAgGBmeBDAECATA/BgsrBgEE
AYLfEwEBATAwMC4GCCsGAQUFBwIBFiJodHRwOi8vY3BzLnJvb3QteDEubGV0c2Vu
Y3J5cHQub3JnMDwGA1UdHwQ1MDMwMaAvoC2GK2h0dHA6Ly9jcmwuaWRlbnRydXN0
LmNvbS9EU1RST09UQ0FYM0NSTC5jcmwwHQYDVR0OBBYEFDadPuCxQPYnLHy/jZ0x
ivZUpkYmMB0GA1UdJQQWMBQGCCsGAQUFBwMBBggrBgEFBQcDAjANBgkqhkiG9w0B
AQsFAAOCAQEAN4CpgPmK2C5pq/RdV9gEdWcvPnPfT9ToucrAMTcn//wyWBWF2wG4
hvPBQxxuqPECZsi4nLQ45VJpyC1NDd0GqGQIMqNdC4N4TLDtd7Yhy8v5JsfEMUbb
6xW4sKeeeKy3afOkel60Xg1/7ndSmppiHqdh+TdJML1hptRgdxGiB8LMpHuW/oM8
akfyt4TkBhA8+Wu8MM6dlJyJ7nHBVnEUFQ4Ni+GzNC/pQSL2+Y9Mq4HHIk2ZFy0W
B8KsVwdeNrERPL+LjhhLde1Et0aL9nlv4CqwXHML2LPgk38j/WllbQ/8HRd2VpB+
JW6Z8JNhcnuBwATHMCeJVCFapoZsPfQQ6Q==
-----END CERTIFICATE-----
"""

RADIUS_DICTONARY = """ATTRIBUTE	User-Name					1	string
ATTRIBUTE	User-Password				2	string
ATTRIBUTE	CHAP-Password				3	octets
ATTRIBUTE	NAS-IP-Address				4	ipaddr
ATTRIBUTE	NAS-Port					5	integer
ATTRIBUTE	Service-Type				6	integer
ATTRIBUTE	Framed-Protocol				7	integer
ATTRIBUTE	Framed-IP-Address			8	ipaddr
ATTRIBUTE	Framed-IP-Netmask			9	ipaddr
ATTRIBUTE	Framed-Routing				10	integer
ATTRIBUTE	Filter-Id					11	string
ATTRIBUTE	Framed-MTU					12	integer
ATTRIBUTE	Framed-Compression			13	integer
ATTRIBUTE	Login-IP-Host				14	ipaddr
ATTRIBUTE	Login-Service				15	integer
ATTRIBUTE	Login-TCP-Port				16	integer
ATTRIBUTE	Reply-Message				18	string
ATTRIBUTE	Callback-Number				19	string
ATTRIBUTE	Callback-Id					20	string
ATTRIBUTE	Framed-Route				22	string
ATTRIBUTE	Framed-IPX-Network			23	ipaddr
ATTRIBUTE	State						24	octets
ATTRIBUTE	Class						25	octets
ATTRIBUTE	Vendor-Specific				26	octets
ATTRIBUTE	Session-Timeout				27	integer
ATTRIBUTE	Idle-Timeout				28	integer
ATTRIBUTE	Termination-Action			29	integer
ATTRIBUTE	Called-Station-Id			30	string
ATTRIBUTE	Calling-Station-Id			31	string
ATTRIBUTE	NAS-Identifier				32	string
ATTRIBUTE	Proxy-State					33	octets
ATTRIBUTE	Login-LAT-Service			34	string
ATTRIBUTE	Login-LAT-Node				35	string
ATTRIBUTE	Login-LAT-Group				36	octets
ATTRIBUTE	Framed-AppleTalk-Link		37	integer
ATTRIBUTE	Framed-AppleTalk-Network	38	integer
ATTRIBUTE	Framed-AppleTalk-Zone		39	string
ATTRIBUTE	Acct-Status-Type			40	integer
ATTRIBUTE	Acct-Delay-Time				41	integer
ATTRIBUTE	Acct-Input-Octets			42	integer
ATTRIBUTE	Acct-Output-Octets			43	integer
ATTRIBUTE	Acct-Session-Id				44	string
ATTRIBUTE	Acct-Authentic				45	integer
ATTRIBUTE	Acct-Session-Time			46	integer
ATTRIBUTE	Acct-Input-Packets			47	integer
ATTRIBUTE	Acct-Output-Packets			48	integer
ATTRIBUTE	Acct-Terminate-Cause		49	integer
ATTRIBUTE	Acct-Multi-Session-Id		50	string
ATTRIBUTE	Acct-Link-Count				51	integer
ATTRIBUTE	Acct-Input-Gigawords		52	integer
ATTRIBUTE	Acct-Output-Gigawords		53	integer
ATTRIBUTE	Event-Timestamp				55	date
ATTRIBUTE	CHAP-Challenge				60	string
ATTRIBUTE	NAS-Port-Type				61	integer
ATTRIBUTE	Port-Limit					62	integer
ATTRIBUTE	Login-LAT-Port				63	integer
ATTRIBUTE	Acct-Tunnel-Connection		68	string
ATTRIBUTE	ARAP-Password				70	string
ATTRIBUTE	ARAP-Features				71	string
ATTRIBUTE	ARAP-Zone-Access			72	integer
ATTRIBUTE	ARAP-Security				73	integer
ATTRIBUTE	ARAP-Security-Data			74	string
ATTRIBUTE	Password-Retry				75	integer
ATTRIBUTE	Prompt						76	integer
ATTRIBUTE	Connect-Info				77	string
ATTRIBUTE	Configuration-Token			78	string
ATTRIBUTE	EAP-Message					79	string
ATTRIBUTE	Message-Authenticator		80	octets
ATTRIBUTE	ARAP-Challenge-Response		84	string
ATTRIBUTE	Acct-Interim-Interval		85	integer
ATTRIBUTE	NAS-Port-Id					87	string
ATTRIBUTE	Framed-Pool					88	string
ATTRIBUTE	NAS-IPv6-Address			95	octets
ATTRIBUTE	Framed-Interface-Id			96	octets
ATTRIBUTE	Framed-IPv6-Prefix			97	octets
ATTRIBUTE	Login-IPv6-Host				98	octets
ATTRIBUTE	Framed-IPv6-Route			99	string
ATTRIBUTE	Framed-IPv6-Pool			100	string
ATTRIBUTE	Framed-IPv6-Pool			100	string
"""

DEMO_LOG_ENTRIES = [
    {
        'id': '56610a2ab0e7307d6a553175',
        'message': 'Started server "West".',
        'timestamp': 1449055271,
    },
    {
        'id': '56610a2ab0e7307d6a55316d',
        'message': 'Started server "East".',
        'timestamp': 1449054471,
    },
    {
        'id': '566106c3b0e7307d6a552ee0',
        'message': 'Created server "West".',
        'timestamp': 1449053618,
    },
    {
        'id': '566106bab0e730539212b4a1',
        'message': 'Created server "East".',
        'timestamp': 1449052968,
    },
    {
        'id': '566106bab0e730539212b4a0',
        'message': 'Created 2 new users.',
        'timestamp': 1449050591,
    },
    {
        'id': '565e8be6b0e730539211c695',
        'message': 'Created 30 new users.',
        'timestamp': 1449049318,
    },
    {
        'id': '565e8bddb0e730519bdf51e1',
        'message': 'Created 30 new users.',
        'timestamp': 1449048575,
    },
    {
        'id': '565e8bddb0e730519bdf51e0',
        'message': 'Created new organization "Links".',
        'timestamp': 1449047691,
    },
    {
        'id': '565e8babb0e730519bdf50fc',
        'message': 'Created new organization "Operations".',
        'timestamp': 1449046292,
    },
    {
        'id': '565e8ba7b0e73045a8aa5bac',
        'message': 'Created new organization "Developers".',
        'timestamp': 1449045128,
    },
    {
        'id': '565e8ba7b0e73045a8aa5bab',
        'message': 'Web server started.',
        'timestamp': 1449044723,
    },
    {
        'id': '565e87eeb0e73045a8aa5885',
        'message': 'Web server started.',
        'timestamp': 1449043571,
    },
]

DEMO_AUDIT_EVENTS = [
    {
        'message': 'User connected to "east"',
        'remote_addr': '12.34.56.78',
        'timestamp': 1449053618,
        'type': 'user_connection',
    },
    {
        'message': 'User temporary profile links created from web console',
        'remote_addr': '12.34.56.78',
        'timestamp': 1449052968,
        'type': 'user_profile',
    },
    {
        'message': 'User created with single sign-on',
        'remote_addr': '12.34.56.78',
        'timestamp': 1449051783,
        'type': 'user_profile',
    },
]

DEMO_ADMIN_AUDIT_EVENTS = [
    {
        'message': 'Single sign-on settings changed',
        'remote_addr': '12.34.56.78',
        'timestamp': 1449054365,
        'type': 'admin_settings',
    },
    {
        'message': 'Administrator username changed',
        'remote_addr': '12.34.56.78',
        'timestamp': 1449053618,
        'type': 'admin_settings',
    },
    {
        'message': 'Administrator password changed',
        'remote_addr': '12.34.56.78',
        'timestamp': 1449052968,
        'type': 'admin_settings',
    },
    {
        'message': 'Administrator login successful',
        'remote_addr': '12.34.56.78',
        'timestamp': 1449051783,
        'type': 'admin_auth',
    },
]

DEMO_LOGS = [
    '[us-east][2016-03-08 04:35:40,616][INFO] Starting server',
    '[us-west][2016-03-08 04:35:56,616][INFO] Starting server',
]

DEMO_OUTPUT = [
    '[us-east] Mon Dec 28 04:01:00 2015 OpenVPN 2.3.6 x86_64-redhat' +
        '-linux-gnu [SSL (OpenSSL)] [LZO] [EPOLL] [PKCS11] [MH] [IPv6] ' +
        'built on Dec 10 2014',
    '[us-east] Mon Dec 28 04:01:00 2015 library versions: OpenSSL 1.0.1k-' +
        'fips 8 Jan 2015, LZO 2.08',
    '[us-east] Mon Dec 28 04:01:00 2015 Control Channel Authentication: ' +
        'tls-auth using INLINE static key file',
    '[us-east] Mon Dec 28 04:01:00 2015 TUN/TAP device tun19 opened',
    '[us-east] Mon Dec 28 04:01:00 2015 do_ifconfig, tt->ipv6=0, ' +
        'tt->did_ifconfig_ipv6_setup=0',
    '[us-east] Mon Dec 28 04:01:00 2015 /sbin/ip link set dev ' +
        'tun19 up mtu 1500',
    '[us-east] Mon Dec 28 04:01:00 2015 /sbin/ip addr add dev ' +
        'tun19 10.100.0.1/16 broadcast 10.100.255.255',
    '[us-east] Mon Dec 28 04:01:00 2015 UDPv4 link local (bound): [undef]',
    '[us-east] Mon Dec 28 04:01:00 2015 UDPv4 link remote: [undef]',
    '[us-east] Mon Dec 28 04:01:00 2015 Initialization Sequence Completed',
]

GROUP_MONGO = 'mongo'
GROUP_FILE = 'file'
GROUP_LOCAL = 'local'

DEFAULT_USERNAME = 'pritunl'
DEFAULT_PASSWORD = 'pritunl'
DEFAULT_CONF_PATH = '/etc/pritunl.conf'
SUBSCRIPTION_UPDATE_RATE = 900
SUB_RESPONSE_TIMEOUT = 10
CLIENT_CONF_VER = 1
MONGO_MESSAGES_SIZE = 100000
MONGO_MESSAGES_MAX = 2048
MONGO_CONNECT_TIMEOUT = 15000
MONGO_SOCKET_TIMEOUT = 30000
AUTH_SIG_STRING_MAX_LEN = 10240
SOCKET_BUFFER = 1024
SERVER_OUTPUT_DELAY = 1.5
SERVER_EVENT_DELAY = 2
IP_REGEX = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
VALID_DH_PARAM_BITS = (1024, 1536, 2048, 3072, 4096)
AUTH_SERVER = 'https://auth.pritunl.com'
ONELOGIN_URL = 'https://api.onelogin.com'
NTP_SERVER = 'ntp.ubuntu.com'
STATIC_FILE_EXTENSIONS = {
    '.css',
    '.eot',
    '.html',
    '.ico',
    '.js',
    '.less',
    '.png',
    '.svg',
    '.ttf',
    '.txt',
    '.woff',
    '.woff2',
}
MOBILE_PLATFORMS = {
    'android',
    'ios',
}
DESKTOP_PLATFORMS = {
    'linux',
    'mac',
    'win',
    'chrome',
}

INFO = 'info'
WARNING = 'warning'
ERROR = 'error'

ADAPTIVE = 'adaptive'
VERSION_NAME = 'version'
OPENSSL_NAME = 'openssl.conf'
INDEX_NAME = 'index'
INDEX_ATTR_NAME = 'index.attr'
SERIAL_NAME = 'serial'
OVPN_CONF_NAME = 'openvpn.conf'
WG_PRIVATE_KEY_NAME = 'wg_private.key'
OVPN_CA_NAME = 'ca.crt'
DH_PARAM_NAME = 'dh_param.pem'
TLS_AUTH_NAME = 'tls_auth.key'
IP_POOL_NAME = 'ip_pool'
SERVER_USER_PREFIX = 'server_'
HOST_USER_PREFIX = 'host_'
SERVER_CERT_NAME = 'server.crt'
SERVER_CHAIN_NAME = 'server.chain'
SERVER_KEY_NAME = 'server.key'
SERVER_DH_NAME = 'server.dh'
SETUP_SERVER_CERT_NAME = 'setup_server.crt'
SETUP_SERVER_KEY_NAME = 'setup_server.key'
SERVER_CONF_NAME = 'server.conf'
MANAGEMENT_SOCKET_NAME = 'pritunl_%s.sock'
KEY_VIEW_NAME = 'key_view.html'
KEY_VIEW_DARK_NAME = 'key_view_dark.html'
DBCONF_NAME = 'dbconf.html'
UPGRADE_NAME = 'upgrade.html'
CONF_TEMP_EXT = '.tmp'
LOG_ARCHIVE_NAME = 'pritunl_log'
SHUT_DOWN = 'shut_down'

CERT_CA = 'ca'
CERT_SERVER = 'server'
CERT_CLIENT = 'client'
CERT_SERVER_POOL = 'server_pool'
CERT_CLIENT_POOL = 'client_pool'

ORG_DEFAULT = 'default'
ORG_POOL = 'pool'

ALL = 'all'

LOCAL_AUTH = 'local'
DUO_AUTH = 'duo'
YUBICO_AUTH = 'yubico'
AZURE_AUTH = 'azure'
AZURE_DUO_AUTH = 'azure_duo'
AZURE_YUBICO_AUTH = 'azure_yubico'
GOOGLE_AUTH = 'google'
GOOGLE_DUO_AUTH = 'google_duo'
GOOGLE_YUBICO_AUTH = 'google_yubico'
AUTHZERO_AUTH = 'authzero'
AUTHZERO_DUO_AUTH = 'authzero_duo'
AUTHZERO_YUBICO_AUTH = 'authzero_yubico'
SLACK_AUTH = 'slack'
SLACK_DUO_AUTH = 'slack_duo'
SLACK_YUBICO_AUTH = 'slack_yubico'
SAML_AUTH = 'saml'
SAML_DUO_AUTH = 'saml_duo'
SAML_YUBICO_AUTH = 'saml_yubico'
SAML_OKTA_AUTH = 'saml_okta'
SAML_OKTA_DUO_AUTH = 'saml_okta_duo'
SAML_OKTA_YUBICO_AUTH = 'saml_okta_yubico'
SAML_ONELOGIN_AUTH = 'saml_onelogin'
SAML_ONELOGIN_DUO_AUTH = 'saml_onelogin_duo'
SAML_ONELOGIN_YUBICO_AUTH = 'saml_onelogin_yubico'
RADIUS_AUTH = 'radius'
RADIUS_DUO_AUTH = 'radius_duo'
PLUGIN_AUTH = 'plugin'

AUTH_TYPES = {
    LOCAL_AUTH,
    DUO_AUTH,
    YUBICO_AUTH,
    AZURE_AUTH,
    AZURE_DUO_AUTH,
    AZURE_YUBICO_AUTH,
    GOOGLE_AUTH,
    GOOGLE_DUO_AUTH,
    GOOGLE_YUBICO_AUTH,
    AUTHZERO_AUTH,
    AUTHZERO_DUO_AUTH,
    AUTHZERO_YUBICO_AUTH,
    SLACK_AUTH,
    SLACK_DUO_AUTH,
    SLACK_YUBICO_AUTH,
    SAML_AUTH,
    SAML_DUO_AUTH,
    SAML_YUBICO_AUTH,
    SAML_OKTA_AUTH,
    SAML_OKTA_DUO_AUTH,
    SAML_OKTA_YUBICO_AUTH,
    SAML_ONELOGIN_AUTH,
    SAML_ONELOGIN_DUO_AUTH,
    SAML_ONELOGIN_YUBICO_AUTH,
    RADIUS_AUTH,
    RADIUS_DUO_AUTH,
    PLUGIN_AUTH,
}

SETTINGS_UPDATED = 'settings_updated'
ADMINS_UPDATED = 'administrators_updated'
ORGS_UPDATED = 'organizations_updated'
USERS_UPDATED = 'users_updated'
LINKS_UPDATED = 'links_updated'
LOG_UPDATED = 'log_updated'
SYSTEM_LOG_UPDATED = 'system_log_updated'
HOSTS_UPDATED = 'hosts_updated'
SERVERS_UPDATED = 'servers_updated'
SERVER_ROUTES_UPDATED = 'server_routes_updated'
SERVER_ORGS_UPDATED = 'server_organizations_updated'
SERVER_HOSTS_UPDATED = 'server_hosts_updated'
SERVER_LINKS_UPDATED = 'server_links_updated'
SERVER_OUTPUT_UPDATED = 'server_output_updated'
SERVER_LINK_OUTPUT_UPDATED = 'server_link_output_updated'
SUBSCRIPTION_PREMIUM_ACTIVE = 'subscription_premium_active'
SUBSCRIPTION_ENTERPRISE_ACTIVE = 'subscription_enterprise_active'
SUBSCRIPTION_ENTERPRISE_PLUS_ACTIVE = 'subscription_enterprise_plus_active'
SUBSCRIPTION_NONE_INACTIVE = 'subscription_none_inactive'
SUBSCRIPTION_PREMIUM_INACTIVE = 'subscription_premium_inactive'
SUBSCRIPTION_ENTERPRISE_INACTIVE = 'subscription_enterprise_inactive'
SUBSCRIPTION_ENTERPRISE_PLUS_INACTIVE = 'subscription_enterprise_plus_inactive'
THEME_LIGHT = 'theme_light'
THEME_DARK = 'theme_dark'

BASH_COLORS = [
    '92',
    '93',
    '94',
    '95',
    '96',
    '91',
    '90',
]

VALID_IP_ENDPOINTS = {
    '5', '9', '13', '17', '21', '25', '29', '33', '37', '41', '45', '49',
    '53', '57', '61', '65', '69', '73', '77', '81', '85', '89', '93', '97',
    '101', '105', '109', '113', '117', '121', '125', '129', '133', '137',
    '141', '145', '149', '153', '157', '161', '165', '169', '173', '177',
    '181', '185', '189', '193', '197', '201', '205', '209', '213', '217',
    '221', '225', '229', '233', '237', '241', '245', '249', '253',
}

CERT_CONF = """\
[ default ]
[ req ]
default_bits = %s
default_md = %s
encrypt_key = no
utf8 = yes
string_mask = utf8only
prompt = no
distinguished_name = req_dn

[ req_dn ]
organizationName = %s
commonName = %s

[ ca_req_ext ]
keyUsage = critical,keyCertSign,cRLSign
basicConstraints = critical,CA:true
subjectKeyIdentifier = hash

[ server_req_ext ]
keyUsage = critical,digitalSignature,keyEncipherment
extendedKeyUsage = serverAuth,clientAuth
subjectKeyIdentifier = hash

[ client_req_ext ]
keyUsage = critical,digitalSignature,keyEncipherment
extendedKeyUsage = clientAuth
subjectKeyIdentifier = hash

[ ca ]
default_ca = root_ca

[ root_ca ]
database = %s
serial = %s
new_certs_dir = %s
certificate = %s
private_key = %s
default_days = 7300
default_crl_days = 365
default_md = %s
policy = ca_policy
crl_extensions = crl_ext

[ ca_policy ]
organizationName = match
commonName = supplied

[ ca_ext ]
keyUsage = critical,keyCertSign,cRLSign
basicConstraints = critical,CA:true
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always

[ crl_ext ]
authorityKeyIdentifier = keyid:always

[ server_ext ]
keyUsage = critical,digitalSignature,keyEncipherment
basicConstraints = CA:false
extendedKeyUsage = serverAuth,clientAuth
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always

[ client_ext ]
keyUsage = critical,digitalSignature,keyEncipherment
basicConstraints = CA:false
extendedKeyUsage = clientAuth
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always
"""

MISSING_PARAMS = 'missing_params'
MISSING_PARAMS_MSG = 'Missing required parameters.'

DEMO_BLOCKED = 'demo_blocked'
DEMO_BLOCKED_MSG = 'Not available in demo.'

AUTH_INVALID = 'auth_invalid'
AUTH_INVALID_MSG = 'Authentication credentials are not valid.'

AUTH_DISABLED = 'auth_disabled'
AUTH_DISABLED_MSG = 'Authentication credentials are disabled.'

AUTH_OTP_REQUIRED = 'auth_otp_required'
AUTH_OTP_REQUIRED_MSG = 'Two-factor authentication required.'

ACME_ERROR = 'acme_error'
ACME_ERROR_MSG = 'Error getting LetsEncrypt certificate check ' + \
    'the logs for more information.'

NETWORK_INVALID = 'network_invalid'
NETWORK_INVALID_MSG = 'Network address is not valid, format must be ' + \
    '"[10,172,192].[0-255,16-31,168].[0-255].0/[8-24]" ' + \
    'such as "10.12.32.0/24".'

NETWORK_WG_INVALID = 'network_wg_invalid'
NETWORK_WG_INVALID_MSG = 'Network WG address is not valid, format must ' + \
    'be "[10,172,192].[0-255,16-31,168].[0-255].0/[8-24]" ' + \
    'such as "10.12.32.0/24".'

NETWORK_WG_CIDR_INVALID = 'network_wg_cidr_invalid'
NETWORK_WG_CIDR_INVALID_MSG = 'Network WG address must use the same CIDR ' \
    'as virtual network.'

LINK_NETWORK_INVALID = 'link_network_invalid'
LINK_NETWORK_INVALID_MSG = 'Network address is invalid, format must be ' + \
    '"10.0.0.0/24".'

BRIDGE_NETWORK_INVALID = '_bridge_network_invalid'
BRIDGE_NETWORK_INVALID_MSG = 'Bridge network start and end must be ' + \
    'inside the server network.'

LOCAL_NETWORK_INVALID = 'local_network_invalid'
LOCAL_NETWORK_INVALID_MSG = 'Local network address is not valid, ' + \
    'format must be "[0-255].[0-255].[0-255].[0-254]/[8-30]" such as ' + \
    '"10.0.0.0/8".'

DNS_SERVER_INVALID = 'dns_server_invalid'
DNS_SERVER_INVALID_MSG = 'DNS server is not valid, ' + \
    'format must be "[0-255].[0-255].[0-255].[0-255]" such as ' + \
    '"8.8.8.8".'

PORT_INVALID = 'port_invalid'
PORT_INVALID_MSG = 'Port number is not valid, must be between 1 and 65535.'

PORT_WG_INVALID = 'port_invalid'
PORT_WG_INVALID_MSG = 'Port number is not valid, must be between 1 and 65535.'

PORT_RESERVED = 'port_reserved'
PORT_RESERVED_MSG = 'Port number is reserved and cannot be used.'

DH_PARAM_BITS_INVALID = 'dh_param_bits_invalid'
DH_PARAM_BITS_INVALID_MSG = 'DH param bits are not valid, must ' + \
    '1024, 1536, 2048, 2048, 3072 or 4096.'

PROTOCOL_INVALID = 'protocol_invalid'
PROTOCOL_INVALID_MSG = 'Protocol is not valid, must be "udp" or "tcp".'

CIPHER_INVALID = 'cipher_invalid'
CIPHER_INVALID_MSG = 'Encryption cipher is invalid.'

HASH_INVALID = 'hash_invalid'
HASH_INVALID_MSG = 'Hash algorithm is invalid.'

NETWORK_LINK_INVALID = 'network_link_invalid'
NETWORK_LINK_INVALID_MSG = 'Network link is not a valid network address.'

NETWORK_LINK_NOT_OFFLINE = 'network_link_not_offline'
NETWORK_LINK_NOT_OFFLINE_MSG = 'All attached servers must be offline to ' + \
    'add a network link.'

USERS_BACKGROUND = 'users_background'
USERS_BACKGROUND_MSG = 'Users will be created in background. This task ' + \
    'will take several seconds for each user being created.'

USERS_BACKGROUND_BUSY = 'users_background_busy'
USERS_BACKGROUND_BUSY_MSG = 'Users are already being created in ' + \
    'background. Wait for task to complete before adding more users.'

AUTH_TOO_MANY = 'auth_too_many'
AUTH_TOO_MANY_MSG = 'Too many authentication attempts.'

PIN_INVALID = 'pin_invalid'
PIN_INVALID_MSG = 'Current pin is invalid.'

PIN_NOT_DIGITS = 'pin_not_digits'
PIN_NOT_DIGITS_MSG = 'Pin must contain only digits.'

PIN_TOO_SHORT = 'pin_too_short'
PIN_TOO_SHORT_MSG = 'Pin is not long enough.'

PIN_IS_DISABLED = 'pin_disabled'
PIN_IS_DISABLED_MSG = 'Pin is disabled.'

PIN_RADIUS = 'pin_radius'
PIN_RADIUS_MSG = 'Pin cannot be used with Radius users.'

PIN_BYPASS_SECONDARY = 'pin_bypass_secondary'
PIN_BYPASS_SECONDARY_MSG = 'Cannot set pin with secondary ' + \
    'authentication bypass enabled.'

TOKEN_INVALID = 'token_invalid'
TOKEN_INVALID_MSG = 'Token is invalid.'

PASSCODE_INVALID = 'passcode_invalid'
PASSCODE_INVALID_MSG = 'Passcode is invalid.'

DUO_FAILED = 'duo_failed'
DUO_FAILED_MSG = 'Duo authentication failed.'

YUBIKEY_INVALID = 'yubikey_invalid'
YUBIKEY_INVALID_MSG = 'YubiKey is invalid.'

YUBIKEY_BYPASS_SECONDARY = 'yubikey_bypass_secondary'
YUBIKEY_BYPASS_SECONDARY_MSG = 'Cannot set YubiKey with secondary ' + \
    'authentication bypass enabled.'

NETWORK_IN_USE = 'network_in_use'
NETWORK_IN_USE_MSG = 'Network address is already in use.'

NETWORK_WG_IN_USE = 'network_WG_in_use'
NETWORK_WG_IN_USE_MSG = 'Network WG address is already in use.'

PORT_PROTOCOL_IN_USE = 'port_protocol_in_use'
PORT_PROTOCOL_IN_USE_MSG = 'Port and protocol is already in use.'

PORT_WG_IN_USE = 'port_wg_protocol_in_use'
PORT_WG_IN_USE_MSG = 'WG Port is already in use.'

BRIDGED_IPV6_INVALID = 'bridged_ipv6_invalid'
BRIDGED_IPV6_INVALID_MSG = 'IPv6 cannot be used with bridged servers.'

BRIDGED_SERVER_LINKS_INVALID = 'bridged_server_links_invalid'
BRIDGED_SERVER_LINKS_INVALID_MSG = 'Server links cannot be used with ' + \
    'bridged servers.'

BRIDGED_NET_LINKS_INVALID = 'bridged_net_links_invalid'
BRIDGED_NET_LINKS_INVALID_MSG = 'Network links cannot be used with ' + \
    'bridged servers.'

BRIDGED_REPLICA_INVALID = 'bridged_replica_invalid'
BRIDGED_REPLICA_INVALID_MSG = 'Cannot have multiple replicas with ' + \
    'bridged servers.'

SERVER_LINKS_NOT_OFFLINE = 'server_links_not_offline'
SERVER_LINKS_NOT_OFFLINE_SETTINGS_MSG = 'All linked servers must be ' + \
    'offline to modify settings.'

SERVER_LINKS_AND_REPLICA = 'server_links_and_replica'
SERVER_LINKS_AND_REPLICA_MSG = 'Cannot have multiple replicas with ' + \
    'linked servers.'

SERVER_VXLAN_NON_NAT = 'server_vxlan_non_nat'
SERVER_VXLAN_NON_NAT_MSG = 'Cannot use VXLan with non-NAT routes.'

SERVER_DOMAIN_NO_DNS = 'server_domain_no_dns'
SERVER_DOMAIN_NO_DNS_MSG = 'Cannot use DNS search domains without ' + \
    'setting DNS servers.'

CLIENT_DNS_MAPPING_NO_DNS = 'client_dns_mapping_no_dns'
CLIENT_DNS_MAPPING_NO_DNS_MSG = 'Cannot use client DNS mapping without ' + \
    'setting DNS servers.'

SERVER_NOT_OFFLINE = 'server_not_offline'
SERVER_NOT_OFFLINE_SETTINGS_MSG = 'Server must be offline to modify settings.'
SERVER_NOT_OFFLINE_ATTACH_ORG_MSG = 'Server must be offline to attach ' + \
    'an organization.'
SERVER_NOT_OFFLINE_DETACH_ORG_MSG = 'Server must be offline to detach ' + \
    'an organization.'
SERVER_NOT_OFFLINE_UNLINK_SERVER_MSG = 'Server must be offline to unlink ' + \
    'a server.'

SERVER_ROUTE_ONLINE = 'server_route_online'
SERVER_ROUTE_ONLINE_MSG = 'Cannot modify routes while server is online.'

SERVER_ROUTE_INVALID = 'server_route_invalid'
SERVER_ROUTE_INVALID_MSG = 'Route network address is not valid.'

SERVER_ROUTE_VIRTUAL_NAT = 'server_route_virtual_nat'
SERVER_ROUTE_VIRTUAL_NAT_MSG = 'Virtual network routes cannot use NAT.'

SERVER_ROUTE_SERVER_LINK_NAT = 'server_route_server_link_nat'
SERVER_ROUTE_SERVER_LINK_NAT_MSG = 'Server link routes cannot modify NAT.'

SERVER_ROUTE_NETWORK_LINK_GATEWAY = 'server_route_network_link_gateway'
SERVER_ROUTE_NETWORK_LINK_GATEWAY_MSG = 'Network link routes cannot use ' + \
    'net gateway.'

SERVER_ROUTE_NET_GATEWAY_NAT = 'server_route_net_gateway_nat'
SERVER_ROUTE_NET_GATEWAY_NAT_MSG = 'Net gateway routes cannot use NAT.'

SERVER_ROUTE_NON_NAT_NETMAP = 'server_route_non_nat_netmap'
SERVER_ROUTE_NON_NAT_NETMAP_MSG = 'Cannot use network mapping without NAT.'

SERVER_LINK_COMMON_HOST = 'server_link_common_host'
SERVER_LINK_COMMON_HOST_MSG = 'Linked servers cannot have a common host.'

SERVER_LINK_COMMON_ROUTE = 'server_link_common_route'
SERVER_LINK_COMMON_ROUTE_MSG = 'Linked servers cannot have a common route.'

EMAIL_NOT_CONFIGURED = 'email_not_configured'
EMAIL_NOT_CONFIGURED_MSG = 'Required email settings have not been ' + \
    'configured, please open settings and configure email.'

EMAIL_FROM_INVALID = 'email_from_invalid'
EMAIL_FROM_INVALID_MSG = 'SMTP server did not accept the from address.'

EMAIL_AUTH_INVALID = 'email_auth_invalid'
EMAIL_AUTH_INVALID_MSG = 'SMTP authentication is invalid.'

IPV6_SUBNET_ONLINE = 'ipv6_subnet_online'
IPV6_SUBNET_ONLINE_MSG = 'IPv6 routed subnet cannot be changed with ' + \
    'IPv6 servers online.'

IPV6_SUBNET_WG_ONLINE = 'ipv6_subnet_wg_online'
IPV6_SUBNET_WG_ONLINE_MSG = 'IPv6 WG routed subnet cannot be changed ' \
    'with IPv6 servers online.'

IPV6_SUBNET_INVALID = 'ipv6_subnet_invalid'
IPV6_SUBNET_INVALID_MSG = 'IPv6 routed subnet is invalid.'

IPV6_SUBNET_WG_INVALID = 'ipv6_subnet_wg_invalid'
IPV6_SUBNET_WG_INVALID_MSG = 'IPv6 WG routed subnet is invalid.'

IPV6_SUBNET_SIZE_INVALID = 'ipv6_subnet_size_invalid'
IPV6_SUBNET_SIZE_INVALID_MSG = 'IPv6 routed subnet size is invalid,' \
    'must be at least /64.'

IPV6_SUBNET_WG_SIZE_INVALID = 'ipv6_subnet_wg_size_invalid'
IPV6_SUBNET_WG_SIZE_INVALID_MSG = 'IPv6 WG routed subnet size is invalid,' \
    'must be at least /64.'

RADIUS_DUO_PASSCODE = 'radius_duo_passcode'
RADIUS_DUO_PASSCODE_MSG = 'Duo passcode cannot be used with Radius.'

DUO_PASSCODE = 'duo_passcode'
DUO_PASSCODE_MSG = 'Duo passcode cannot be when only authenticating with Duo.'

SUBSCRIPTION_SERVER_ERROR = 'subscription_server_error'
SUBSCRIPTION_SERVER_ERROR_MSG = 'Unable to connect to ' + \
    'subscription server, please try again later.'

LICENSE_INVALID = 'license_invalid'
LICENSE_INVALID_MSG = 'License key is invalid'

MONGODB_URI_INVALID = 'mongodb_uri_invalid'
MONGODB_URI_INVALID_MSG = 'MongoDB URI is invalid.'

MONGODB_CONNECT_ERROR = 'mongodb_connect_error'
MONGODB_CONNECT_ERROR_MSG = 'Unable to connect to MongoDB server.'

MONGODB_AUTH_ERROR = 'mongodb_auth_error'
MONGODB_AUTH_ERROR_MSG = 'Unable to authenticate to the MongoDB server.'

SETUP_KEY_INVALID = 'setup_key_invalid'
SETUP_KEY_INVALID_MSG = 'Setup key is invalid.'

DUO_USER_INVALID = 'duo_user_invalid'
DUO_USER_INVALID_MSG = 'Username is invalid.'

SSO_ORG_NULL = 'sso_org_null'
SSO_ORG_NULL_MSG = 'The SSO organization must be set.'

NO_ADMINS_ENABLED = 'no_admins_enabled'
NO_ADMINS_ENABLED_MSG = 'At least one super administrator must be enabled.'

NO_SUPER_USERS = 'no_super_users'
NO_SUPER_USERS_MSG = 'There must be at least one super user.'

NO_ADMINS = 'no_admins'
NO_ADMINS_MSG = 'At least one super administrator must exist.'

ADMIN_USERNAME_EXISTS = 'admin_username_exists'
ADMIN_USERNAME_EXISTS_MSG = 'Administrator username already exists.'

REQUIRES_SUPER_USER = 'requires_super_user'
REQUIRES_SUPER_USER_MSG = 'This administrator action can only be ' + \
    'performed by a super user.'

CANNOT_DISABLE_AUTIDING = 'cannot_disable_autiding'
CANNOT_DISABLE_AUTIDING_MSG = 'Auditing cannot be disabled from web console.'

RANDOM_ONE = (
    'snowy',
    'restless',
    'calm',
    'ancient',
    'summer',
    'evening',
    'guarded',
    'lively',
    'thawing',
    'autumn',
    'thriving',
    'patient',
    'winter',
)
RANDOM_TWO = (
    'waterfall',
    'meadow',
    'skies',
    'waves',
    'fields',
    'stars',
    'dreams',
    'refuge',
    'forest',
    'plains',
    'waters',
    'plateau',
    'thunder',
)

CIPHERS = {
    'none': 'cipher none',
    'bf128': 'cipher BF-CBC',
    'bf256': 'cipher BF-CBC\nkeysize 256',
    'aes128': 'cipher AES-128-CBC',
    'aes192': 'cipher AES-192-CBC',
    'aes256': 'cipher AES-256-CBC',
}

SERVER_CIPHERS_OLD = {
    'none': 'cipher none',
    'bf128': 'cipher BF-CBC',
    'bf256': 'cipher BF-CBC\nkeysize 256',
    'aes128': 'cipher AES-128-CBC',
    'aes192': 'cipher AES-192-CBC',
    'aes256': 'cipher AES-256-CBC',
}
SERVER_CIPHERS = {
    'none': 'cipher none',
    'bf128': 'cipher BF-CBC',
    'bf256': 'cipher BF-CBC\nkeysize 256',
    'aes128': 'cipher AES-128-CBC\nncp-ciphers AES-128-GCM:AES-128-CBC',
    'aes192': 'cipher AES-192-CBC\nncp-ciphers AES-192-GCM:AES-192-CBC',
    'aes256': 'cipher AES-256-CBC\nncp-ciphers AES-256-GCM:AES-256-CBC',
}

HASHES = {
    'none': 'none',
    'md5': 'MD5',
    'sha1': 'SHA1',
    'sha256': 'SHA256',
    'sha512': 'SHA512',
}

ONC_CIPHERS = {
    'none': 'none',
    'bf128': 'BF-CBC',
    'bf256': 'BF-CBC',
    'aes128': 'AES-128-CBC',
    'aes192': 'AES-192-CBC',
    'aes256': 'AES-256-CBC',
}

JUMBO_FRAMES = {
    False: '',
    True: 'tun-mtu 9000\nfragment 0\nmssfix 0\n',
}

OVPN_INLINE_SERVER_CONF_OLD = """\
port %s
proto %s
dev %s
%s
management %s unix
management-client-auth
auth-user-pass-optional
topology subnet
tls-version-min 1.2
max-clients %s
ping %s
ping-restart %s
push "ping %s"
push "ping-restart %s"
persist-tun
%s
auth %s
status-version 2
script-security 2
sndbuf 393216
rcvbuf 393216
reneg-sec 2592000
hash-size 1024 1024
txqueuelen 1000
verb %s
mute %s
"""

OVPN_INLINE_SERVER_CONF = """\
ignore-unknown-option ncp-ciphers
port %s
proto %s
dev %s
%s
management %s unix
management-client-auth
auth-user-pass-optional
topology subnet
tls-version-min 1.2
max-clients %s
ping %s
ping-restart %s
push "ping %s"
push "ping-restart %s"
persist-tun
%s
auth %s
status-version 2
script-security 2
sndbuf 393216
rcvbuf 393216
reneg-sec 2592000
hash-size 1024 1024
txqueuelen 1000
verb %s
mute %s
"""

OVPN_INLINE_CLIENT_CONF = """\
%s
setenv UV_ID %s
setenv UV_NAME %s
client
dev %s
dev-type %s
%s
nobind
persist-tun
%s
auth %s
verb 2
mute 3
push-peer-info
ping %s
ping-restart %s
hand-window 70
server-poll-timeout %s
reneg-sec 2592000
sndbuf 393216
rcvbuf 393216
remote-cert-tls server
"""

OVPN_ONC_CLIENT_CONF = """\
{
  "Type": "UnencryptedConfiguration",
  "NetworkConfigurations": [
%s
  ],
  "Certificates": [
%s
  ]
}
"""

OVPN_ONC_NET_CONF = """\
    {
      "GUID": "%s",
      "Name": "%s",
      "Type": "VPN",
      "VPN": {
        "Host": "%s",
        "Type": "OpenVPN",
        "OpenVPN": {
          "AuthRetry": "interact",
          "Auth": "%s",
          "Cipher": "%s",
          "ClientCertType": "Ref",
          "ClientCertRef": "%s",
          "CompLZO": "%s",%s
          "Port": %s,
          "Proto": "%s",
          "PushPeerInfo": true,
          "RenegSec": 2592000,
          "ServerCARefs": [
%s
          ],
          "ServerPollTimeout": 4,%s
          "RemoteCertTLS": "server",%s
          "Verb": "2"
        }
      }
    }"""

OVPN_ONC_AUTH_NONE = """
          "SaveCredentials": false,
          "UserAuthenticationType": "Password",
          "Username": "%s","""

OVPN_ONC_AUTH_OTP = """
          "SaveCredentials": false,
          "UserAuthenticationType": "OTP",
          "Username": "%s","""

OVPN_ONC_AUTH_PASS = """
          "SaveCredentials": false,
          "UserAuthenticationType": "Password",
          "Username": "%s","""

OVPN_ONC_AUTH_PASS_OTP = """
          "SaveCredentials": false,
          "UserAuthenticationType": "Password",
          "Username": "%s","""

OVPN_ONC_CA_CERT = """\
    {
      "GUID": "%s",
      "Type": "Authority",
      "X509": "%s"
    }"""

OVPN_ONC_CLIENT_CERT = """\
    {
      "GUID": "%s",
      "Type": "Client",
      "PKCS12": "%s"
    }"""

OVPN_INLINE_LINK_CONF = """\
client
setenv UV_ID %s
setenv UV_NAME %s
dev %s
dev-type %s
%s
nobind
persist-tun
%s
auth %s
verb %s
mute %s
push-peer-info
ping %s
ping-restart %s
hand-window 70
server-poll-timeout %s
reneg-sec 2592000
sndbuf 393216
rcvbuf 393216
remote-cert-tls server
"""

IPSEC_SECRET = '%s %s : PSK "%s"'

IPSEC_CONN = """\
conn %s
	ikelifetime=8h
	keylife=1h
	rekeymargin=9m
	keyingtries=%%forever
	authby=secret
	keyexchange=ikev2
	mobike=no
	dpddelay=10s
	dpdtimeout=30s
	dpdaction=restart
	left=%%defaultroute
	leftid=%s
	leftsubnet=%s
	right=%s
	rightid=%s
	rightsubnet=%s
	auto=start

"""

UBNT_CONF = """\
set vpn ipsec auto-firewall-nat-exclude enable

set vpn ipsec ike-group pritunl lifetime 10800
set vpn ipsec ike-group pritunl key-exchange ikev2
set vpn ipsec ike-group pritunl proposal 1 dh-group 19
set vpn ipsec ike-group pritunl proposal 1 encryption aes128
set vpn ipsec ike-group pritunl proposal 1 hash sha256

set vpn ipsec esp-group pritunl lifetime 3600
set vpn ipsec esp-group pritunl pfs dh-group19
set vpn ipsec esp-group pritunl proposal 1 encryption aes128
set vpn ipsec esp-group pritunl proposal 1 hash sha256
"""

UBNT_PEER = """
set vpn ipsec site-to-site peer %s authentication mode pre-shared-secret
set vpn ipsec site-to-site peer %s authentication pre-shared-secret %s
set vpn ipsec site-to-site peer %s connection-type initiate
set vpn ipsec site-to-site peer %s local-address any
set vpn ipsec site-to-site peer %s ike-group pritunl
"""

UBNT_SUBNET = """set vpn ipsec site-to-site peer %s tunnel %d esp-group pritunl
set vpn ipsec site-to-site peer %s tunnel %d local prefix %s
set vpn ipsec site-to-site peer %s tunnel %d remote prefix %s
"""

NDPPD_CONF = """\
route-ttl 20000
address-ttl 20000
proxy %s {
  router yes
  timeout 1000
  ttl 30000
  rule %s {
    static
  }
}
"""

KEY_LINK_EMAIL_TEXT = """\
Your vpn profile can be downloaded from the temporary link below. You may also directly import your profiles in the Pritunl client using the temporary URI link.

Profile Link: {key_link}
URI Profile Link: {uri_link}"""

KEY_LINK_EMAIL_HTML = """\
<p>Your vpn profile can be downloaded from the temporary link below.
You may also directly import your profiles in the Pritunl client using the
temporary URI link.<br><br>
Profile Link: <a href="{key_link}">{key_link}</a><br>
URI Profile Link: <a href="{uri_link}">{uri_link}</a></p>

<div itemscope itemtype="http://schema.org/EmailMessage">
  <div itemprop="action" itemscope itemtype="http://schema.org/ViewAction">
    <link itemprop="url" href="{key_link}"></link>
    <meta itemprop="name" content="View Profile"></meta>
  </div>
  <meta itemprop="description" content="View Pritunl profile and configuration information"></meta>
</div>"""
