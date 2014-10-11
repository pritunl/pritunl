import subprocess
import os
import time

nodes = [
    'node0',
    'node1',
    'node2',
    'node3',
]
processes = []

try:
    for node in nodes:
        process_output = open('./var/%s.output' % node, 'wb')
        process = subprocess.Popen([
                'vagrant',
                'ssh',
                node,
                '-c', 'cd /vagrant; sudo python2 -u server.py',
            ],
            stdout=process_output,
            stderr=process_output,
        )
        processes.append(process)

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
    print 'Exiting...'
    for node in nodes:
        process = subprocess.Popen([
                'vagrant',
                'ssh',
                node,
                '-c', 'sudo killall -q python2 | true',
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        processes.append(process)

    for process in processes:
        process.wait()

    subprocess.check_call(['reset'])
