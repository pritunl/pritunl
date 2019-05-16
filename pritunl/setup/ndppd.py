from pritunl.helpers import *
from pritunl.constants import *
from pritunl import logger
from pritunl import settings
from pritunl import utils

import os
import threading
import subprocess
import time

default_interface6 = None

@interrupter
def _default_interface_thread():
    global default_interface6

    while True:
        iface6 = None
        iface6_alt = None

        try:
            routes_output = utils.check_output_logged(
                ['route', '-n', '-A', 'inet6'])
        except subprocess.CalledProcessError:
            logger.exception('Failed to get IPv6 routes', 'setup')
            time.sleep(1)
            continue

        for line in routes_output.splitlines():
            line_split = line.split()

            if len(line_split) < 7:
                continue

            if line_split[0] == '::/0':
                if iface6 or line_split[6] == 'lo':
                    continue
                iface6 = line_split[6]

            if line_split[0] == 'ff00::/8':
                if iface6_alt or line_split[6] == 'lo':
                    continue
                iface6_alt = line_split[6]

        default_interface6 = iface6 or iface6_alt

        time.sleep(10)

@interrupter
def _ndppd_thread():
    conf_path = utils.get_temp_path() + '_ndppd.conf'
    time.sleep(3)

    while True:
        process = None

        try:
            host_routed_subnet6 = settings.local.host.routed_subnet6
            host_proxy_ndp = settings.local.host.proxy_ndp
            iface6 = default_interface6

            if not host_routed_subnet6 or not host_proxy_ndp:
                yield interrupter_sleep(3)
                continue

            if not iface6:
                logger.error('Default IPv6 interface not available', 'setup')
                yield interrupter_sleep(3)
                continue

            with open(conf_path, 'w') as conf_file:
                conf_file.write(NDPPD_CONF % (
                    iface6,
                    host_routed_subnet6,
                ))

            process = subprocess.Popen([
                'ndppd',
                '-c', conf_path,
            ])

            while True:
                if host_routed_subnet6 != \
                        settings.local.host.routed_subnet6 or \
                        host_proxy_ndp != settings.local.host.proxy_ndp or \
                        iface6 != default_interface6:
                    process.terminate()
                    yield interrupter_sleep(2)
                    process.kill()
                    process = None
                    break
                elif process.poll() is not None:
                    output = None
                    try:
                        output = process.stdout.readall()
                        output += process.stderr.readall()
                    except:
                        pass

                    if check_global_interrupt():
                        return

                    logger.error(
                        'Ndppd service stopped unexpectedly', 'setup',
                        output=output,
                    )
                    process = None

                    yield interrupter_sleep(1)

                    break

                time.sleep(0.5)
                yield
        except GeneratorExit:
            if process:
                process.terminate()
                time.sleep(1)
                process.kill()
            return
        except:
            logger.exception('Error in ndppd service', 'setup')
        finally:
            try:
                os.remove(conf_path)
            except:
                pass

        yield interrupter_sleep(1)

def setup_ndppd():
    threading.Thread(target=_default_interface_thread).start()
    threading.Thread(target=_ndppd_thread).start()
