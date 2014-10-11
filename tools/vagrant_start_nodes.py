import subprocess
import os
import time
import signal
import sys

nodes = sys.argv[1:]
exit_handled = False

for node in nodes:
    with open('var/%s.output' % node, 'w') as node_file:
        pass

def signal_handler(signum=None, frame=None):
    global exit_handled
    if exit_handled:
        return
    exit_handled = True

    print 'Exiting...'

    processes = []
    for node in nodes:
        process = subprocess.Popen(
            ('screen -d -m /bin/bash -c \'vagrant ssh %s -c ' +
                '"sudo killall openvpn; ' +
                'sudo killall python2; '
                'sudo killall -s9 python2"\'') % node,
            shell=True,
        )
        processes.append(process)

    for process in processes:
        process.wait()

    time.sleep(1)

    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

try:
    for node in nodes:
        subprocess.check_call(
            ('screen -d -m /bin/bash -c \'vagrant ssh %s -c ' +
                '"cd /vagrant; sudo python2 -u server.py"' +
                ' > var/%s.output\'') % (node, node),
            shell=True,
        )

    print '##############################################################'
    print '#                                                            #'
    print '#                      /$$   /$$                         /$$ #'
    print '#                     |__/  | $$                        | $$ #'
    print '#   /$$$$$$   /$$$$$$  /$$ /$$$$$$   /$$   /$$ /$$$$$$$ | $$ #'
    print '#  /$$__  $$ /$$__  $$| $$|_  $$_/  | $$  | $$| $$__  $$| $$ #'
    print '# | $$  \ $$| $$  \__/| $$  | $$    | $$  | $$| $$  \ $$| $$ #'
    print '# | $$  | $$| $$      | $$  | $$ /$$| $$  | $$| $$  | $$| $$ #'
    print '# | $$$$$$$/| $$      | $$  |  $$$$/|  $$$$$$/| $$  | $$| $$ #'
    print '# | $$____/ |__/      |__/   \___/   \______/ |__/  |__/|__/ #'
    print '# | $$                                                       #'
    print '# | $$                                                       #'
    print '# |__/                                                       #'
    print '#                                                            #'
    print '##############################################################'
    print 'Server nodes running...'

    while True:
        time.sleep(1)
finally:
    signal_handler()
