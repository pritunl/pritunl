from pritunl.monitoring.utils import get_servers

from pritunl import settings
from pritunl import logger

import threading
import influxdb_client
import influxdb_client.client.write_api

_queue = []
_queue_lock = threading.Lock()
_client = None
_cur_influxdb_url = None
_cur_influxdb_org = None
_cur_influxdb_bucket = None
_cur_influxdb_token = None
_write_options = influxdb_client.client.write_api.SYNCHRONOUS

def insert_point(measurement, tags, fields):
    _queue_lock.acquire()
    try:
        if not _client:
            return

        point = influxdb_client.Point(
            settings.app.influxdb_prefix + measurement
        )

        for key, val in tags.items():
            point.tag(key, val)

        for key, val in fields.items():
            point.field(key, val)

        _queue.append(point)
    finally:
        _queue_lock.release()

def write_queue():
    global _queue

    _queue_lock.acquire()
    try:
        if not _queue:
            return
        queue = _queue
        _queue = []
        client = _client
    finally:
        _queue_lock.release()

    if client:
        try:
            write_api = client.write_api(write_options=_write_options)
            write_api.write(bucket=_cur_influxdb_bucket, record=queue)
        except:
            _queue_lock.acquire()
            try:
                _queue = queue + _queue
            finally:
                _queue_lock.release()
            raise

def connect():
    global _client
    global _cur_influxdb_url
    global _cur_influxdb_org
    global _cur_influxdb_bucket
    global _cur_influxdb_token

    influxdb_url = settings.app.influxdb_url
    influxdb_org = settings.app.influxdb_org
    influxdb_bucket = settings.app.influxdb_bucket
    influxdb_token = settings.app.influxdb_token
    if influxdb_url == _cur_influxdb_url and \
            influxdb_org == _cur_influxdb_org and \
            influxdb_bucket == _cur_influxdb_bucket and \
            influxdb_token == _cur_influxdb_token:
        return

    if not influxdb_url:
        _queue_lock.acquire()
        try:
            _client = None
        finally:
            _queue_lock.release()
        _cur_influxdb_url = influxdb_url
        _cur_influxdb_org = influxdb_org
        _cur_influxdb_bucket = influxdb_bucket
        _cur_influxdb_token = influxdb_token
        return

    logger.info('Connecting to InfluxDB', 'monitoring',
        influxdb_url=influxdb_url,
        influxdb_org=influxdb_org,
        influxdb_bucket=influxdb_bucket,
    )

    _client = influxdb_client.InfluxDBClient(
        url=influxdb_url,
        org=influxdb_org,
        token=influxdb_token,
    )

    _cur_influxdb_url = influxdb_url
    _cur_influxdb_org = influxdb_org
    _cur_influxdb_bucket = influxdb_bucket
    _cur_influxdb_token = influxdb_token

def init():
    try:
        connect()
    except:
        logger.exception('InfluxDB initial connection error',
            'monitoring',
            influxdb_uri=settings.app.influxdb_uri,
        )
