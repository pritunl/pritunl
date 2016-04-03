from pritunl.helpers import *
from pritunl import app
from pritunl import utils
from pritunl import settings
from pritunl import logger

import threading

@interrupter
def _web_watch_thread():
    yield interrupter_sleep(5)

    error_count = 0
    while True:
        while True:
            url = ''
            if settings.app.server_ssl:
                verify = False
                url += 'https://'
            else:
                url += 'http://'
                verify = True
            url += 'localhost:%s/ping' % settings.app.server_port

            try:
                resp = utils.request.get(
                    url,
                    timeout=1,
                    verify=verify,
                )

                if resp.status_code != 200:
                    logger.error('Failed to ping web server, bad status',
                        'watch',
                        url=url,
                        status_code=resp.status_code,
                        content=resp.content,
                    )
                    break
            except:
                logger.exception('Failed to ping web server', 'watch',
                    url=url,
                )
                break

            error_count = 0
            yield interrupter_sleep(3)

        error_count += 1
        if error_count > 1:
            error_count = 0
            logger.error('Web server non-responsive, restarting...', 'watch')
            app.restart_server()
            yield interrupter_sleep(10)
        else:
            yield interrupter_sleep(2)

def start_web_watch():
    threading.Thread(target=_web_watch_thread).start()
