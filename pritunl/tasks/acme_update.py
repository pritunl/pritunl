from pritunl import task
from pritunl import logger
from pritunl import acme
from pritunl import app
from pritunl import utils
from pritunl import settings

class AcmeUpdate(task.Task):
    type = 'acme_update'

    def task(self):
        acme_domain = settings.app.acme_domain

        if not acme_domain:
            return

        if not settings.app.acme_timestamp:
            logger.exception(
                'Failed to update acme certificate. Timestamp not set',
                'tasks',
                acme_domain=acme_domain,
            )
            return

        if not settings.app.acme_key:
            logger.exception(
                'Failed to update acme certificate. Account key not set',
                'tasks',
                acme_domain=acme_domain,
            )
            return

        if utils.time_now() - settings.app.acme_timestamp < \
                settings.app.acme_renew:
            return

        logger.info(
            'Updating acme certificate', 'tasks',
            acme_domain=acme_domain,
        )

        acme.update_acme_cert()
        app.update_server()

task.add_task(AcmeUpdate, hours=4, minutes=35, run_on_start=True)
