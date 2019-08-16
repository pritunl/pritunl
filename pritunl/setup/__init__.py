from pritunl.helpers import *
from pritunl.setup.clean import setup_clean
from pritunl.setup.local import setup_local
from pritunl.setup.vault import setup_vault
from pritunl.setup.server import setup_server
from pritunl.setup.mongo import setup_mongo, upsert_indexes
from pritunl.setup.boto_conf import setup_boto_conf
from pritunl.setup.cache import setup_cache
from pritunl.setup.temp_path import setup_temp_path
from pritunl.setup.logger import setup_logger
from pritunl.setup.signal_handler import setup_signal_handler
from pritunl.setup.public_ip import setup_public_ip
from pritunl.setup.poolers import setup_poolers
from pritunl.setup.host import setup_host
from pritunl.setup.server_listeners import setup_server_listeners
from pritunl.setup.settings import setup_settings
from pritunl.setup.dns import setup_dns
from pritunl.setup.ndppd import setup_ndppd
from pritunl.setup.monitoring import setup_monitoring
from pritunl.setup.host_fix import setup_host_fix
from pritunl.setup.subscription import setup_subscription
from pritunl.setup.runners import setup_runners
from pritunl.setup.handlers import setup_handlers
from pritunl.setup.check import setup_check
from pritunl.setup.plugins import setup_plugins
from pritunl.setup.demo import setup_demo

import resource

def setup_all():
    from pritunl import logger

    setup_local()
    setup_logger()

    try:
        setup_clean()
        setup_temp_path()
        setup_signal_handler()
        setup_vault()
        setup_server()
        setup_mongo()
        setup_settings()
        setup_boto_conf()
        setup_public_ip()
        setup_host()
        setup_cache()
        setup_server_listeners()
        setup_dns()
        setup_monitoring()
        setup_poolers()
        setup_host_fix()
        setup_subscription()
        setup_ndppd()
        setup_runners()
        setup_handlers()
        setup_check()
        setup_plugins()

        setup_demo()

        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        if soft < 25000 or hard < 25000:
            logger.warning(
                'Open file ulimit is lower then recommended',
                'setup',
            )
    except:
        logger.exception('Pritunl setup failed', 'setup')
        set_global_interrupt()
        raise

def setup_db():
    setup_local()

    try:
        setup_logger()
        setup_mongo()
    except:
        from pritunl import logger
        logger.exception('Pritunl setup failed', 'setup')
        raise

def setup_db_host():
    setup_local()

    try:
        setup_logger()
        setup_mongo()
        setup_host()
    except:
        from pritunl import logger
        logger.exception('Pritunl setup failed', 'setup')
        raise

def setup_loc():
    setup_local()

    try:
        setup_logger()
    except:
        from pritunl import logger
        logger.exception('Pritunl setup failed', 'setup')
        raise
