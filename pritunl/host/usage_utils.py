from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
import logging
import subprocess

logger = logging.getLogger(APP_NAME)

def get_proc_stat():
    try:
        with open('/proc/stat') as stat_file:
            return stat_file.readline().split()[1:]
    except:
        logger.exception('Failed to read proc stat')

def calc_cpu_usage(last_proc_stat, proc_stat):
    try:
        deltas = [int(x) - int(y) for x, y in zip(
            proc_stat, last_proc_stat)]
        total = sum(deltas)
        return float(total - deltas[3]) / total
    except:
        logger.exception('Failed to calculate cpu usage')
    return 0

def get_mem_usage():
    try:
        free = subprocess.check_output(['free']).split()
        return float(free[15]) / float(free[7])
    except:
        logger.exception('Failed to get memory usage')
    return 0
