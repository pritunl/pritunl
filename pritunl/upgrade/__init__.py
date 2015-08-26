from pritunl.upgrade.upgrade_1_4 import upgrade_1_4

from pritunl import logger
from pritunl import utils

def upgrade_server():
    if utils.get_db_ver_int() < utils.get_int_ver('1.4.0.0'):
        logger.info('Running 1.4 database upgrade', 'upgrade')
        upgrade_1_4()
        utils.set_db_ver('1.4.0.0')
    else:
        logger.info('No upgrade needed', 'upgrade')
