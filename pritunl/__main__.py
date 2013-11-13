import optparse
import sys
import os
import pritunl

def pritunl_daemon():
    parser = optparse.OptionParser()
    parser.add_option('-d', '--daemon', action='store_true',
        help='Daemonize process')
    parser.add_option('-p', '--pidfile', type='string',
        help='Path to create pid file')
    parser.add_option('-c', '--conf', type='string',
        help='Path to configuration file')
    (options, args) = parser.parse_args()

    if options.daemon:
        pid = os.fork()
        if pid > 0:
            if options.pidfile:
                with open(options.pidfile, 'w') as pid_file:
                    pid_file.write('%s' % pid)
            sys.exit(0)
    else:
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

    if options.conf:
        conf_path = options.conf
    else:
        conf_path = '/etc/pritunl.conf'

    pritunl.app_server.conf_path = conf_path
    pritunl.app_server.run_server()
