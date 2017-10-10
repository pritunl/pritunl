from pritunl import utils
from pritunl import logger

import datetime

def get_period_timestamp(period, timestamp):
    timestamp -= datetime.timedelta(microseconds=timestamp.microsecond,
            seconds=timestamp.second)

    if period == '1m':
        return timestamp
    elif period == '5m':
        return timestamp - datetime.timedelta(
            minutes=timestamp.minute % 5)
    elif period == '30m':
        return timestamp - datetime.timedelta(
            minutes=timestamp.minute % 30)
    elif period == '2h':
        return timestamp - datetime.timedelta(
            hours=timestamp.hour % 2, minutes=timestamp.minute)
    elif period == '1d':
        return timestamp - datetime.timedelta(
            hours=timestamp.hour, minutes=timestamp.minute)

def get_period_max_timestamp(period, timestamp):
    timestamp -= datetime.timedelta(microseconds=timestamp.microsecond,
            seconds=timestamp.second)

    if period == '1m':
        return timestamp - datetime.timedelta(hours=6)
    elif period == '5m':
        return timestamp - datetime.timedelta(
            minutes=timestamp.minute % 5) - datetime.timedelta(days=1)
    elif period == '30m':
        return timestamp - datetime.timedelta(
            minutes=timestamp.minute % 30) - datetime.timedelta(days=7)
    elif period == '2h':
        return timestamp - datetime.timedelta(
            hours=timestamp.hour % 2,
            minutes=timestamp.minute) - datetime.timedelta(days=30)
    elif period == '1d':
        return timestamp - datetime.timedelta(
            hours=timestamp.hour,
            minutes=timestamp.minute) - datetime.timedelta(days=365)

def get_proc_stat():
    try:
        with open('/proc/stat') as stat_file:
            return stat_file.readline().split()[1:]
    except:
        logger.exception('Failed to read proc stat', 'host')

def calc_cpu_usage(last_proc_stat, proc_stat):
    try:
        deltas = [int(x) - int(y) for x, y in zip(
            proc_stat, last_proc_stat)]
        total = sum(deltas)
        return float(total - deltas[3]) / total
    except:
        logger.exception('Failed to calculate cpu usage', 'host')
    return 0

def get_mem_usage():
    try:
        free = utils.check_output_logged(['free']).split()
        return float(free[8]) / float(free[7])
    except:
        logger.exception('Failed to get memory usage', 'host')
    return 0
