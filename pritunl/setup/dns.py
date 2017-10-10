from pritunl.helpers import *
from pritunl import settings
from pritunl import logger

import os
import threading
import subprocess
import time

@interrupter
def _dns_thread():
    from pritunl import host

    while True:
        process = None

        try:
            if not host.dns_mapping_servers:
                yield interrupter_sleep(3)
                continue

            start = time.time()

            yield

            process = subprocess.Popen(
                ['pritunl-dns'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=dict(os.environ, **{
                    'DB': settings.conf.mongodb_uri,
                    'DB_PREFIX': settings.conf.mongodb_collection_prefix or '',
                }),
            )

            while True:
                if not host.dns_mapping_servers:
                    process.terminate()
                    yield interrupter_sleep(3)
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
                        'DNS mapping service stopped unexpectedly', 'setup',
                        output=output,
                    )
                    process = None

                    yield interrupter_sleep(1)

                    break
                elif time.time() - start > settings.app.dns_server_restart:
                    def kill_process():
                        process.kill()
                    timer = threading.Timer(3, kill_process)
                    timer.start()

                    process.terminate()
                    process.wait()

                    timer.cancel()

                    process = None
                    break
        except GeneratorExit:
            if process:
                process.terminate()
                time.sleep(1)
                process.kill()
            return
        except:
            logger.exception('Error in dns service', 'setup')

        yield interrupter_sleep(1)

def setup_dns():
    threading.Thread(target=_dns_thread).start()
