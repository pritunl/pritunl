from pritunl.upgrade.upgrade_1_4 import upgrade_1_4
from pritunl.upgrade.upgrade_1_5 import upgrade_1_5
from pritunl.upgrade.upgrade_1_17 import upgrade_1_17
from pritunl.upgrade.upgrade_1_18 import upgrade_1_18
from pritunl.upgrade.upgrade_1_19 import upgrade_1_19
from pritunl.upgrade.utils import *

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

    if utils.get_db_ver_int() < utils.get_int_ver('1.17.0.0'):
        upgraded = True
        logger.info('Running 1.17 database upgrade', 'upgrade')
        upgrade_1_17()
        utils.set_db_ver('1.17.0.0')

    if utils.get_db_ver_int() < utils.get_int_ver('1.18.0.0'):
        upgraded = True
        logger.info('Running 1.18 database upgrade', 'upgrade')
        upgrade_1_18()
        utils.set_db_ver('1.18.0.0')

    if utils.get_db_ver_int() < utils.get_int_ver('1.19.0.0'):
        upgraded = True
        logger.info('Running 1.19 database upgrade', 'upgrade')
        upgrade_1_19()
        utils.set_db_ver('1.19.0.0')

    if not upgraded:
        logger.info('No upgrade needed', 'upgrade')
