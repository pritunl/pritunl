from constants import *
from cache import cache_db
import os
import logging

logger = logging.getLogger(APP_NAME)

class Config:
    bool_options = set()
    int_options = set()
    float_options = set()
    path_options = set()
    str_options = set()
    list_options = set()
    default_options = {}
    chmod_mode = None
    cached = False
    cache_prefix = None

    def __init__(self, path=None):
        self.all_options = self.bool_options | self.int_options | \
            self.float_options | self.path_options | self.str_options
        self._conf_path = path
        self._loaded = False
        self.set_state(SAVED)

    def __setattr__(self, name, value):
        if name != 'all_options' and name in self.all_options:
            self.set_state(UNSAVED)
        self.__dict__[name] = value

    def __getattr__(self, name):
        if name in self.all_options:
            if not self._loaded:
                self.load()
            if name not in self.__dict__:
                if name in self.default_options:
                    return self.default_options[name]
                if name in self.list_options:
                    self.__dict__[name] = []
                else:
                    return
        elif name not in self.__dict__:
            raise AttributeError('Config instance has no attribute %r' % name)
        return self.__dict__[name]

    def get_state(self):
        return self._state

    def set_state(self, state):
        self._state = state

    def get_path(self):
        return self._conf_path

    def set_path(self, path):
        self._conf_path = path

    def _encode_line(self, name, value):
        if name in self.bool_options:
            value = 'true' if value else 'false'
        elif name in self.list_options:
            value = ','.join(value)

        return '%s=%s\n' % (name, value)

    def _decode_bool(self, value):
        value = value.lower()
        if value in {'true', 't', 'yes', 'y'}:
            return True
        elif value in {'false', 'f', 'no', 'n'}:
            return False
        else:
            raise ValueError('Value is not boolean')

    def _decode_int(self, value):
        return int(value)

    def _decode_float(self, value):
        return float(value)

    def _decode_path(self, value):
        try:
            value = os.path.normpath(value)
        except AttributeError:
            logger.error('Failed to normalize path. %r' % {
                'path': value,
            })
        return value

    def _decode_list(self, value):
        return filter(None, value.split(','))

    def _decode_line(self, line):
        line_split = line.split('=')
        name = line_split[0]
        value = '='.join(line_split[1:])

        if value:
            if name not in self.all_options:
                raise ValueError('Unknown option')

            if not value:
                raise ValueError('Empty option')

            if name in self.list_options:
                values = self._decode_list(value)

                decoder = None
                if name in self.int_options:
                    decoder = self._decode_int
                elif name in self.float_options:
                    decoder = self._decode_float
                elif name in self.bool_options:
                    decoder = self._decode_bool
                elif name in self.path_options:
                    decoder = self._decode_path

                if decoder:
                    for i, value in enumerate(values):
                        values[i] = decoder(value)

                value = values
            elif name in self.str_options:
                pass
            elif name in self.int_options:
                value = self._decode_int(value)
            elif name in self.float_options:
                value = self._decode_float(value)
            elif name in self.bool_options:
                value = self._decode_bool(value)
            elif name in self.path_options:
                value = self._decode_path(value)

        else:
            value = [] if name in self.list_options else None

        return name, value

    def get_cache_key(self, suffix=None):
        if not self.cache_prefix:
            raise AttributeError('Cached config object requires cache_prefix')
        key = '%s-%s' % (self.cache_prefix, self.id)
        if suffix:
            key += '-%s' % suffix
        return key

    def clear_cache(self):
        cache_db.remove(self.get_cache_key('cached'))
        cache_db.remove(self.get_cache_key())

    def load(self, merge=False):
        logger.debug('Loading config. %r' % {
            'path': self._conf_path,
        })
        self._loaded = True

        if self.cached:
            if not hasattr(self, 'id'):
                raise ValueError('Object ID is required for caching')
            if cache_db.get(self.get_cache_key('cached')) == 't':
                if merge:
                    for name, value in cache_db.dict_get_all(
                            self.get_cache_key()).iteritems():
                        if name in self.__dict__:
                            continue
                        self.__dict__[name] = value
                else:
                    self.__dict__.update(cache_db.dict_get_all(
                        self.get_cache_key()))
                return

        try:
            with open(self._conf_path) as config:
                for line in config:
                    line = line.rstrip('\n')

                    if line.strip() == '':
                        continue
                    elif line[0] == '#':
                        continue
                    elif '=' in line:
                        pass
                    else:
                        logger.warning('Ignoring invalid line. %r' % {
                            'line': line,
                        })
                        continue

                    try:
                        name, value = self._decode_line(line)
                        if merge and name in self.__dict__:
                            continue
                        self.__dict__[name] = value
                        if self.cached:
                            cache_db.dict_set(self.get_cache_key(),
                                name, value)
                    except ValueError:
                        logger.warning('Ignoring invalid line. %r' % {
                            'line': line,
                        })
        except IOError:
            if not merge:
                raise

        if self.cached:
            cache_db.set(self.get_cache_key('cached'), 't')

    def commit(self):
        logger.debug('Committing config.')
        if not self._loaded:
            self.load(True)

        try:
            temp_conf_path = self._conf_path + CONF_TEMP_EXT
            with open(temp_conf_path, 'w') as config:
                if self.chmod_mode:
                    os.chmod(temp_conf_path, self.chmod_mode)

                for name in self.all_options:
                    if name not in self.__dict__:
                        continue
                    value = self.__dict__[name]
                    if value is None:
                        continue
                    if self.cached:
                        cache_db.dict_set(self.get_cache_key(), name, value)
                    config.write(self._encode_line(name, value))
            os.rename(temp_conf_path, self._conf_path)
        except:
            try:
                os.remove(temp_conf_path)
            except OSError:
                pass
            raise

        self.set_state(SAVED)
