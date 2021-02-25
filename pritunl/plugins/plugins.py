from pritunl.plugins.utils import *
from pritunl.plugins import example

from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import callqueue
from pritunl import settings
from pritunl import logger

import imp
import os

_queue = None
_has_plugins = False
_handlers = {}

def init():
    global _queue
    global _has_plugins
    global _handlers

    _queue = callqueue.CallQueue(maxsize=settings.app.plugin_queue_size)
    _queue.start(settings.app.plugin_queue_threads)
    _has_plugins = True
    call_types = set(get_functions(example).keys())

    modules = []
    plugin_dir = settings.app.plugin_directory
    plugins_required = set(
        x.strip() for x in (settings.app.plugin_requred or '').split(',') if x)
    plugins_loaded = set()

    if os.path.exists(plugin_dir):
        for file_name in os.listdir(plugin_dir):
            file_path = os.path.join(plugin_dir, file_name)
            file_name, file_ext = os.path.splitext(file_name)
            if file_ext != '.py':
                continue
            logger.info('Loading plugin', 'plugins',
                name=file_name,
            )
            plugins_loaded.add(file_name)
            modules.append(imp.load_source('plugin_' + file_name, file_path))

    missing_plugins = plugins_required - plugins_loaded
    if missing_plugins:
        try:
            logger.error('Missing required plugins', 'plugins',
                missing=list(missing_plugins),
            )
        finally:
            set_global_interrupt()
        raise PluginMissing(
            'Missing required plugins %s' % list(missing_plugins))

    for module in modules:
        for call_type, handler in get_functions(module).items():
            if call_type not in call_types:
                continue
            if call_type not in _handlers:
                _handlers[call_type] = [handler]
            else:
                _handlers[call_type].append(handler)

def _event(event_type, **kwargs):
    for handler in _handlers[event_type]:
        try:
            handler(**kwargs)
        except:
            logger.exception('Error in plugin handler', 'plugins',
                handler=event_type,
            )

def event(event_type, **kwargs):
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return
    if not _has_plugins or event_type not in _handlers:
        return
    _queue.put(_event, event_type, **kwargs)

def caller(caller_type, **kwargs):
    if not _has_plugins or caller_type not in _handlers:
        return

    returns = []
    for handler in _handlers[caller_type]:
        returns.append(handler(**kwargs))
    return returns
