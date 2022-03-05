from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import utils
from pritunl import logger

import subprocess

def sysctl_upsert(key, value, required=True):
    try:
        output = utils.check_output_logged(['sysctl', key])
    except subprocess.CalledProcessError:
        logger.exception('Failed to read sysctl value',
            'server', key=key, value=value,
        )
        output = ''

    for line in output.split('\n'):
        if ('%s =' % key) in line:
            if line.split('=')[-1].strip() == value:
                return

    try:
        utils.check_output_logged(
            ['sysctl', '-w', '%s=%s' % (key, value)])
    except subprocess.CalledProcessError:
        logger.exception('Failed to update sysctl value', 'server',
            key=key, value=value,
        )
        if required:
            raise
