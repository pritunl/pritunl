from pritunl.setup.local import setup_local
from pritunl.setup.clear_temp import setup_clear_temp
from pritunl.setup.app import setup_app
from pritunl.setup.server import setup_server
from pritunl.setup.mongo import setup_mongo
from pritunl.setup.temp_path import setup_temp_path
from pritunl.setup.logger import setup_logger
from pritunl.setup.signal_handler import setup_signal_handler
from pritunl.setup.public_ip import setup_public_ip
from pritunl.setup.poolers import setup_poolers
from pritunl.setup.host import setup_host
from pritunl.setup.runners import setup_runners
from pritunl.setup.handlers import setup_handlers
from pritunl.setup.server_cert import setup_server_cert
from pritunl import settings

def setup_all():
    setup_local()
    setup_clear_temp()
    setup_logger()
    setup_app()
    setup_signal_handler()
    setup_server()
    setup_mongo()
    setup_temp_path()
    setup_host()
    setup_public_ip()
    setup_poolers()
    setup_runners()
    setup_handlers()

    if settings.conf.ssl:
        setup_server_cert()

def setup_db():
    setup_local()
    setup_clear_temp()
    setup_app()
    setup_logger()
    setup_mongo()
