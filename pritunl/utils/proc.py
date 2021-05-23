from pritunl.constants import *

import subprocess
import threading

class Process(object):
    def __init__(self, *args, **kwargs):
        if 'stdout' in kwargs or 'stderr' in kwargs:
            raise ValueError('Output arguments not allowed, '
                'it will be overridden')

        try:
            self._ignore_states = kwargs.pop('ignore_states')
        except KeyError:
            self._ignore_states = None

        self._args = args
        self._kwargs = kwargs
        self._process = None
        self._event = threading.Event()
        self._stdoutdata = None
        self._stderrdata = None
        self._return_code = None

    def _proc_thread(self):
        from pritunl import logger
        cmd = None

        try:
            cmd = self._kwargs.get('args', self._args[0])

            self._process = subprocess.Popen(
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                *self._args, **self._kwargs
            )

            stdoutdata, stderrdata = self._process.communicate()
            return_code = self._process.poll()

            self._stdoutdata = stdoutdata.decode()
            self._stderrdata = stderrdata.decode()
            self._return_code = return_code

            self._event.set()
        except:
            logger.exception('Popen exception', 'utils',
                cmd=cmd,
            )

    def run(self, timeout=None):
        from pritunl import logger

        thread = threading.Thread(target=self._proc_thread)
        thread.daemon = True
        thread.start()

        self._event.wait(timeout)

        cmd = self._kwargs.get('args', self._args[0])

        if not self._event.is_set():
            logger.error('Popen process timeout', 'utils',
                cmd=cmd,
                timeout=timeout,
            )
            try:
                self._process.kill()
            except:
                pass

            raise subprocess.CalledProcessError(-99, cmd, output='')
        elif self._return_code:
            if self._ignore_states:
                for ignore_state in self._ignore_states:
                    if ignore_state in self._stdoutdata or \
                            ignore_state in self._stderrdata:
                        return self._stdoutdata

            logger.error('Popen returned error exit code', 'utils',
                cmd=cmd,
                timeout=timeout,
                return_code=self._return_code,
                stdout=self._stdoutdata,
                stderr=self._stderrdata,
            )

            raise subprocess.CalledProcessError(
                self._return_code, cmd, output=self._stdoutdata)
