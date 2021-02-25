from pritunl import utils
from pritunl import logger

import subprocess
import time

def setup_clean():
    try:
        try:
            utils.check_call_silent([
                'killall',
                'openvpn',
            ])
        except subprocess.CalledProcessError:
            pass

        try:
            utils.check_call_silent([
                'killall',
                'openssl',
            ])
        except subprocess.CalledProcessError:
            pass

        try:
            utils.check_call_silent([
                'killall',
                'pritunl-dns',
            ])
        except subprocess.CalledProcessError:
            pass

        try:
            utils.check_call_silent([
                'killall',
                'pritunl-web',
            ])
        except subprocess.CalledProcessError:
            pass

        time.sleep(2)

        try:
            utils.check_call_silent([
                'killall',
                '-s9',
                'openvpn',
            ])
        except subprocess.CalledProcessError:
            pass

        try:
            utils.check_call_silent([
                'killall',
                '-s9',
                'openssl',
            ])
        except subprocess.CalledProcessError:
            pass

        try:
            utils.check_call_silent([
                'killall',
                '-s9',
                'pritunl-dns',
            ])
        except subprocess.CalledProcessError:
            pass

        try:
            utils.check_call_silent([
                'killall',
                '-s9',
                'pritunl-web',
            ])
        except subprocess.CalledProcessError:
            pass



        output = utils.check_output([
            'ip',
            '-o',
            'link',
            'show',
        ])

        for line in output.splitlines():
            iface_name = line.split(':')
            if len(iface_name) < 2:
                continue
            iface_name = iface_name[1].strip()

            if not iface_name.startswith('pxlan'):
                continue

            try:
                utils.check_call_silent([
                    'ip',
                    'link',
                    'set',
                    'down',
                    iface_name,
                ])
            except subprocess.CalledProcessError:
                pass

            try:
                utils.check_call_silent([
                    'ip',
                    'link',
                    'del',
                    iface_name,
                ])
            except subprocess.CalledProcessError:
                pass



        output = utils.check_output([
            'iptables-save',
        ])

        table = None
        for line in output.splitlines():
            line = line.strip()

            if line in ('*nat', '*filter'):
                table = line[1:]
                continue

            if '--comment pritunl' not in line:
                continue

            try:
                utils.check_call_silent([
                    'iptables -t %s -D %s' % (table, line[3:]),
                ], shell=True)
            except subprocess.CalledProcessError:
                pass
    except:
        logger.exception('Server clean failed', 'setup')

