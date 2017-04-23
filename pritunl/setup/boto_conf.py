from pritunl import settings

import boto

def setup_boto_conf():
    boto.config.add_section('Boto')
    boto.config.set('Boto', 'num_retries', '2')
    boto.config.set('Boto', 'http_socket_timeout',
        str(int(settings.app.aws_timeout)))
