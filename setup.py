from setuptools import setup
import os
import sys
import copy
import shlex
import shutil
import fileinput

VERSION = '1.30.2817.44'
PATCH_DIR = 'build'
install_systemd = True
install_upstart = False
install_sysvinit = False

prefix = sys.prefix
for arg in copy.copy(sys.argv):
    if arg.startswith('--prefix'):
        prefix = os.path.normpath(shlex.split(arg)[0].split('=')[-1])
    elif arg == '--no-systemd':
        sys.argv.remove('--no-systemd')
        install_systemd = False
    elif arg == '--upstart':
        sys.argv.remove('--upstart')
        install_upstart = True
    elif arg == '--sysvinit':
        sys.argv.remove('--sysvinit')
        install_sysvinit = True

if not os.path.exists('build'):
    os.mkdir('build')

main_css_path = os.path.join('www/vendor/dist/css',
    os.listdir('www/vendor/dist/css')[0])
main_js_path = os.path.join('www/vendor/dist/js',
    sorted(os.listdir('www/vendor/dist/js'))[0])

data_files = [
    ('/etc', ['data/etc/pritunl.conf']),
    ('/var/log', [
        'data/var/pritunl.log',
        'data/var/pritunl.log.1',
    ]),
    ('/usr/share/pritunl/www', [
        'www/dbconf.html',
        'www/key_view.html',
        'www/key_view_dark.html',
        'www/duo.html',
        'www/yubico.html',
        'www/login.html',
        'www/upgrade.html',
        'www/vendor/dist/index.html',
        'www/vendor/dist/robots.txt',
        'www/logo.png',
    ]),
    ('/usr/share/pritunl/www/css', [main_css_path]),
    ('/usr/share/pritunl/www/fonts', [
        'www/vendor/dist/fonts/FontAwesome.otf',
        'www/vendor/dist/fonts/fontawesome-webfont.eot',
        'www/vendor/dist/fonts/fontawesome-webfont.svg',
        'www/vendor/dist/fonts/fontawesome-webfont.ttf',
        'www/vendor/dist/fonts/fontawesome-webfont.woff',
        'www/vendor/dist/fonts/fontawesome-webfont.woff2',
        'www/vendor/dist/fonts/fredoka-one.eot',
        'www/vendor/dist/fonts/fredoka-one.woff',
        'www/vendor/dist/fonts/glyphicons-halflings-regular.eot',
        'www/vendor/dist/fonts/glyphicons-halflings-regular.svg',
        'www/vendor/dist/fonts/glyphicons-halflings-regular.ttf',
        'www/vendor/dist/fonts/glyphicons-halflings-regular.woff',
        'www/vendor/dist/fonts/ubuntu.eot',
        'www/vendor/dist/fonts/ubuntu.woff',
        'www/vendor/dist/fonts/ubuntu-bold.eot',
        'www/vendor/dist/fonts/ubuntu-bold.woff',
    ]),
    ('/usr/share/pritunl/www/js', [
        main_js_path,
        'www/vendor/dist/js/require.min.js',
    ]),
]

patch_files = []
if install_sysvinit:
    data_files.append(('/etc/init.d', ['data/init.d.sysvinit/pritunl']))

if install_upstart:
    patch_files.append('%s/pritunl.conf' % PATCH_DIR)
    data_files.append(('/etc/init', ['%s/pritunl.conf' % PATCH_DIR]))
    if not install_sysvinit:
        data_files.append(('/etc/init.d', ['data/init.d.upstart/pritunl']))
    shutil.copy('data/init/pritunl.conf', '%s/pritunl.conf' % PATCH_DIR)

if install_systemd:
    patch_files.append('%s/pritunl.service' % PATCH_DIR)
    data_files.append(('/etc/systemd/system',
        ['%s/pritunl.service' % PATCH_DIR]))
    shutil.copy('data/systemd/pritunl.service',
        '%s/pritunl.service' % PATCH_DIR)

for file_name in patch_files:
    for line in fileinput.input(file_name, inplace=True):
        line = line.replace('%PREFIX%', prefix)
        print(line.rstrip('\n'))

packages = ['pritunl']

for dir_name in os.listdir('pritunl'):
    if os.path.isdir(os.path.join('pritunl', dir_name)):
        packages.append('pritunl.%s' % dir_name)

setup(
    name='pritunl',
    version=VERSION,
    description='Enterprise VPN server',
    long_description=open('README.md').read(),
    author='Pritunl',
    author_email='contact@pritunl.com',
    url='https://github.com/pritunl/pritunl',
    download_url='https://github.com/pritunl/pritunl/archive/%s.tar.gz' % (
        VERSION),
    keywords='pritunl, vpn server, distributed vpn server, ' +
        'enterprise vpn server, open source vpn server, ' +
        'virtual private network, virtual networks, openvpn client, ' +
        'openvpn server, vpn tutorial',
    packages=packages,
    license=open('LICENSE').read(),
    zip_safe=False,
    data_files=data_files,
    entry_points={
        'console_scripts': ['pritunl = pritunl.__main__:main'],
    },
    platforms=[
        'Linux',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: End Users/Desktop',
        'License :: Other/Proprietary License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Networking',
    ],
)
