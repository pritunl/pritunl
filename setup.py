from setuptools import setup
import os
import sys
import copy
import shlex
import shutil
import fileinput
import pritunl

PATCH_DIR = 'build'
INSTALL_UPSTART = True
INSTALL_SYSTEMD = True

prefix = sys.prefix
for arg in copy.copy(sys.argv):
    if arg.startswith('--prefix'):
        prefix = os.path.normpath(shlex.split(arg)[0].split('=')[-1])
    elif arg == '--no-upstart':
        sys.argv.remove('--no-upstart')
        INSTALL_UPSTART = False
    elif arg == '--no-systemd':
        sys.argv.remove('--no-systemd')
        INSTALL_SYSTEMD = False

if not os.path.exists('build'):
    os.mkdir('build')

data_files = [
    ('/etc', ['data/etc/pritunl.conf']),
    ('/var/lib/pritunl', ['data/var/pritunl.db']),
    ('/var/log', ['data/var/pritunl.log']),
    ('/usr/share/pritunl/www', ['www/dist/favicon.ico']),
    ('/usr/share/pritunl/www', ['www/dist/index.html']),
    ('/usr/share/pritunl/www', ['www/dist/robots.txt']),
    ('/usr/share/pritunl/www/fonts',
        ['www/dist/fonts/fredoka-one.eot']),
    ('/usr/share/pritunl/www/fonts',
        ['www/dist/fonts/fredoka-one.woff']),
    ('/usr/share/pritunl/www/fonts',
        ['www/dist/fonts/glyphicons-halflings-regular.eot']),
    ('/usr/share/pritunl/www/fonts',
        ['www/dist/fonts/glyphicons-halflings-regular.svg']),
    ('/usr/share/pritunl/www/fonts',
        ['www/dist/fonts/glyphicons-halflings-regular.ttf']),
    ('/usr/share/pritunl/www/fonts',
        ['www/dist/fonts/glyphicons-halflings-regular.woff']),
    ('/usr/share/pritunl/www/fonts', ['www/dist/fonts/ubuntu-bold.eot']),
    ('/usr/share/pritunl/www/fonts', ['www/dist/fonts/ubuntu-bold.woff']),
    ('/usr/share/pritunl/www/fonts', ['www/dist/fonts/ubuntu.eot']),
    ('/usr/share/pritunl/www/fonts', ['www/dist/fonts/ubuntu.woff']),
    ('/usr/share/pritunl/www/css', ['www/dist/css/main.css']),
    ('/usr/share/pritunl/www/js', ['www/dist/js/main.js']),
    ('/usr/share/pritunl/www/js', ['www/dist/js/require.min.js']),
]

patch_files = []
if INSTALL_UPSTART:
    patch_files.append('%s/pritunl.conf' % PATCH_DIR)
    data_files.append(('/etc/init', ['%s/pritunl.conf' % PATCH_DIR]))
    shutil.copy('data/init/pritunl.conf', '%s/pritunl.conf' % PATCH_DIR)
if INSTALL_SYSTEMD:
    patch_files.append('%s/pritunl.service' % PATCH_DIR)
    data_files.append(('/etc/systemd/system',
        ['%s/pritunl.service' % PATCH_DIR]))
    shutil.copy('data/systemd/pritunl.service',
        '%s/pritunl.service' % PATCH_DIR)

for file_name in patch_files:
    for line in fileinput.input(file_name, inplace=True):
        line = line.replace('%PREFIX%', prefix)
        print line.rstrip('\n')

setup(
    name='pritunl',
    version=pritunl.__version__,
    description='Simple openvpn server',
    long_description=open('README.rst').read(),
    author='Zachary Huff',
    author_email='zach.huff.386@gmail.com',
    url='https://github.com/zachhuff386/pritunl',
    download_url='https://github.com/zachhuff386/pritunl/archive/%s.tar.gz' % (
        pritunl.__version__),
    keywords='openvpn, vpn, management, server, web interface',
    packages=['pritunl', 'pritunl.handlers'],
    license=open('LICENSE').read(),
    zip_safe=False,
    install_requires=[
        'flask>=0.6',
        'cherrypy>=3.2.0',
    ],
    data_files=data_files,
    entry_points={
        'console_scripts': ['pritunl = pritunl.__main__:pritunl_daemon'],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Networking',
    ],
)
