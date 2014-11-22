import pritunl

import optparse
import sys
import os

USAGE = """Usage: pritunl [command] [options]
Command Help: pritunl [command] --help

Commands:
  start                 Start server
  version               Print the version and exit
  reset-password        Reset administrator password
  reconfigure           Reconfigure database connection
  logs                  View server logs"""

def pritunl_daemon(default_conf=None):
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
    else:
        cmd = 'start'

    parser = optparse.OptionParser(usage=USAGE)

    if cmd == 'start':
        parser.add_option('-d', '--daemon', action='store_true',
            help='Daemonize process')
        parser.add_option('-p', '--pidfile', type='string',
            help='Path to create pid file')
        parser.add_option('-c', '--conf', type='string',
            help='Path to configuration file')
        parser.add_option('-q', '--quiet', action='store_true',
            help='Suppress logging output')
    elif cmd == 'logs':
        parser.add_option('--archive', action='store_true',
            help='Archive log file')
        parser.add_option('--tail', action='store_true',
            help='Tail log file')
        parser.add_option('--limit', type='int',
            help='Limit log lines')

    (options, args) = parser.parse_args()

    pritunl.set_conf_path(options.conf or default_conf)

    if cmd == 'version':
        print '%s v%s' % (pritunl.__title__, pritunl.__version__)
        sys.exit(0)
    elif cmd == 'reset-password':
        from pritunl.constants import DEFAULT_USERNAME, DEFAULT_PASSWORD
        from pritunl import setup
        from pritunl import auth

        setup.setup_db()
        username, password = auth.reset_password()

        print 'Administrator password successfully reset:\n' + \
            '  username: "%s"\n  password: "%s"' % (username, password)

        sys.exit(0)
    elif cmd == 'reconfigure':
        from pritunl import setup
        from pritunl import settings
        setup.setup_db()

        settings.conf.mongodb_uri = None
        settings.conf.commit()

        print 'Database configuration successfully reset'

        sys.exit(0)
    elif cmd == 'logs':
        from pritunl.constants import DEFAULT_USERNAME, DEFAULT_PASSWORD
        from pritunl import setup
        from pritunl import logger
        setup.setup_db()

        log_view = logger.LogView()

        if options.archive:
            if len(args) > 1:
                archive_path = args[1]
            else:
                archive_path = './'
            print 'Log archived to: ' + log_view.archive_log(archive_path,
                options.limit)
        elif options.tail:
            for msg in log_view.tail_log_lines():
                print msg
        else:
            print log_view.get_log_lines(options.limit)

        sys.exit(0)
    elif cmd != 'start':
        raise ValueError('Invalid command')

    from pritunl import settings

    if options.quiet:
        settings.local.quiet = True

    if options.daemon:
        pid = os.fork()
        if pid > 0:
            if options.pidfile:
                with open(options.pidfile, 'w') as pid_file:
                    pid_file.write('%s' % pid)
            sys.exit(0)
    elif not options.quiet:
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

    pritunl.init_server()
