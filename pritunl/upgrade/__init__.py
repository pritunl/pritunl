from pritunl import logger

def upgrade_server():
    # if utils.get_db_ver_int() < 1000306624015:
    #     logger.info('Running 0.10.x database upgrade', 'upgrade')
    #     upgrade_0_10_x()
    #     utils.set_db_ver('1.0.0')
    # else:
    #     logger.info('DB version changed, no upgrade needed', 'upgrade')
    logger.info('No upgrade needed', 'upgrade')
