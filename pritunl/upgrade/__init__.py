from pritunl.upgrade.upgrade_1_4 import upgrade_1_4
from pritunl.upgrade.upgrade_1_5 import upgrade_1_5

from pritunl import logger
from pritunl import utils

def upgrade_server():
    upgraded = False

    if utils.get_db_ver_int() < utils.get_int_ver('1.4.0.0'):
        upgraded = True
        logger.info('Running 1.4 database upgrade', 'upgrade')
        upgrade_1_4()
        utils.set_db_ver('1.4.0.0')

    if utils.get_db_ver_int() < utils.get_int_ver('1.5.0.0'):
        upgraded = True
        logger.info('Running 1.5 database upgrade', 'upgrade')
        upgrade_1_5()
        utils.set_db_ver('1.5.0.0')

    if not upgraded:
        logger.info('No upgrade needed', 'upgrade')
