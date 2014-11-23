from pritunl.upgrade.upgrade_0_10_x import upgrade_0_10_x

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import utils
from pritunl import logger

def upgrade_server():
    if utils.get_db_ver_int() < 100000000:
        logger.info('Running 0.10.x database upgrade', 'upgrade')
        upgrade_0_10_x()
        utils.set_db_ver('1.0.0')
