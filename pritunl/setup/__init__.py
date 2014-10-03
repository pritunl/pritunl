from pritunl.setup.local import setup_local
from pritunl.setup.mongo import setup_mongo
from pritunl.setup.temp_path import setup_temp_path
from pritunl.setup.logger import setup_logger
from pritunl.setup.public_ip import setup_public_ip
from pritunl.setup.updates import setup_updates
from pritunl.setup.handlers import setup_handlers
from pritunl.setup.poolers import setup_poolers
from pritunl.setup.queue_runner import setup_queue_runner
from pritunl.setup.transaction_runner import setup_transaction_runner
from pritunl.setup.task_runner import setup_task_runner
from pritunl.setup.listener import setup_listener
from pritunl.setup.host import setup_host
from pritunl.setup.server_cert import setup_server_cert
from pritunl.settings import settings

def setup_all():
    setup_local()
    setup_mongo()
    setup_temp_path()
    setup_logger()
    setup_public_ip()
    setup_updates()
    setup_handlers()
    setup_poolers()
    setup_queue_runner()
    setup_transaction_runner()
    setup_task_runner()
    setup_listener()
    setup_host()

    if settings.conf.ssl:
        setup_server_cert()
