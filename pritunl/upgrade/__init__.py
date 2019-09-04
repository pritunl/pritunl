from pritunl.upgrade.upgrade_1_4 import upgrade_1_4
from pritunl.upgrade.upgrade_1_5 import upgrade_1_5
from pritunl.upgrade.upgrade_1_17 import upgrade_1_17
from pritunl.upgrade.upgrade_1_18 import upgrade_1_18
from pritunl.upgrade.upgrade_1_24 import upgrade_1_24
from pritunl.upgrade.utils import *
from pritunl.constants import *

from pritunl import logger
from pritunl import utils

def upgrade_server():
    upgraded = False

    if not SE_MODE:
        if utils.get_db_ver_int() < utils.get_int_ver('1.4.0.0'):
            upgraded = True
            logger.info('Running 1.4 database upgrade', 'upgrade')
            upgrade_1_4()
            utils.set_db_ver('1.4.0.0', '1.4.0.0')

        if utils.get_db_ver_int() < utils.get_int_ver('1.5.0.0'):
            upgraded = True
            logger.info('Running 1.5 database upgrade', 'upgrade')
            upgrade_1_5()
            utils.set_db_ver('1.5.0.0', '1.5.0.0')

        if utils.get_db_ver_int() < utils.get_int_ver('1.17.0.0'):
            upgraded = True
            logger.info('Running 1.17 database upgrade', 'upgrade')
            upgrade_1_17()
            utils.set_db_ver('1.17.0.0', '1.17.0.0')

        if utils.get_db_ver_int() < utils.get_int_ver('1.18.0.0'):
            upgraded = True
            logger.info('Running 1.18 database upgrade', 'upgrade')
            upgrade_1_18()
            utils.set_db_ver('1.18.0.0', '1.18.0.0')

        if utils.get_db_ver_int() < utils.get_int_ver('1.24.0.0'):
            upgraded = True
            logger.info('Running 1.24 database upgrade', 'upgrade')
            upgrade_1_24()
            utils.set_db_ver('1.24.0.0', '1.24.0.0')

    if not upgraded and utils.get_db_ver(False):
        logger.info('No upgrade needed', 'upgrade')
