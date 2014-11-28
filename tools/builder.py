import optparse
import datetime
import re
import sys
import json
import os
import subprocess
import time
import getpass
import requests

UBUNTU_RELEASES = [
    'trusty', # 14.04
    'precise', # 12.04
    'utopic', # 14.10
]

USAGE = """Usage: builder [command] [options]
Command Help: builder [command] --help

Commands:
  version               Print the version and exit
  set-version           Set current version
  build                 Build and release"""

INIT_PATH = 'pritunl/__init__.py'
CHANGES_PATH = 'CHANGES'
DEBIAN_CHANGELOG_PATH = 'debian/changelog'
BUILD_KEYS_PATH = 'tools/build_keys.json'
ARCH_PKGBUILD = 'arch/production/PKGBUILD'
ARCH_DEV_PKGBUILD = 'arch/dev/PKGBUILD'
CENTOS_PKGSPEC = 'centos/pritunl.spec'
CENTOS_DEV_PKGSPEC = 'centos/pritunl-dev.spec'
PRIVATE_KEY_NAME = 'private_key.asc'
WWW_DIR = 'www'
STYLES_DIR = 'www/styles'

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def vagrant_popen(cmd, cwd=None, name='node0'):
    if cwd:
        cmd = 'cd /vagrant/%s; %s' % (cwd, cmd)
    return subprocess.Popen("vagrant ssh --command='%s' %s" % (cmd, name),
        shell=True, stdin=subprocess.PIPE)

def vagrant_check_call(cmd, cwd=None, name='node0'):
    if cwd:
        cmd = 'cd /vagrant/%s; %s' % (cwd, cmd)
    return subprocess.check_call("vagrant ssh --command='%s' %s" % (cmd, name),
        shell=True, stdin=subprocess.PIPE)

def wget(url, cwd=None):
    subprocess.check_call(['wget', url], cwd=cwd)

def rm_tree(path):
    subprocess.check_call(['rm', '-rf', path])

def tar_extract(archive_path, cwd=None):
    subprocess.check_call(['tar', 'xfz', archive_path], cwd=cwd)

def tar_compress(archive_path, in_path, cwd=None):
    subprocess.check_call(['tar', 'cfz', archive_path, in_path], cwd=cwd)

def get_int_ver(version):
    ver = re.findall(r'\d+', version)

    if 'alpha' in version:
        ver[3] = str(int(ver[3]) + 1000)
    elif 'beta' in version:
        ver[3] = str(int(ver[3]) + 2000)
    elif 'rc' in version:
        ver[3] = str(int(ver[3]) + 3000)
    elif len(ver) > 3:
        ver[3] = ver[3].zfill(4)
    else:
        ver.append('0000')

    return int(''.join([x.zfill(2) for x in ver]))


# Load build keys
with open(BUILD_KEYS_PATH, 'r') as build_keys_file:
    build_keys = json.loads(build_keys_file.read().strip())
    github_owner = build_keys['github_owner']
    github_token = build_keys['github_token']
    mongodb_uri = build_keys['mongodb_uri']
    private_key = build_keys['private_key']

mongo_client = pymongo.MongoClient(mongodb_uri)
mongo_db = mongo_client.get_default_database()
releases_db = mongo_db.releases

# Get package info
with open(INIT_PATH, 'r') as init_file:
    for line in init_file.readlines():
        line = line.strip()

        if line[:9] == '__title__':
            app_name = line.split('=')[1].replace("'", '').strip()
            pkg_name = app_name.replace('_', '-')

        elif line[:10] == '__author__':
            maintainer = line.split('=')[1].replace("'", '').strip()

        elif line[:9] == '__email__':
            maintainer_email = line.split('=')[1].replace("'", '').strip()

        elif line[:11] == '__version__':
            key, val = line.split('=')
            cur_version = line.split('=')[1].replace("'", '').strip()

# Parse args
if len(sys.argv) > 1:
    cmd = sys.argv[1]
else:
    cmd = 'version'

parser = optparse.OptionParser(usage=USAGE)
(options, args) = parser.parse_args()

build_num = 0

if cmd == 'version':
    print '%s v%s' % (app_name, cur_version)
    sys.exit(0)


elif cmd == 'set-version':
    new_version = args[1]
    is_snapshot = 'snapshot' in new_version

    # Check for duplicate version
    response = requests.get(
        'https://api.github.com/repos/%s/%s/releases' % (
            github_owner, pkg_name),
        headers={
            'Authorization': 'token %s' % github_token,
            'Content-type': 'application/json',
        },
        data=json.dumps({
            'tag_name': new_version,
            'name': '%s v%s' % (pkg_name, new_version),
            'body': 'Snapshot release',
            'prerelease': True,
        }),
    )

    if response.status_code != 200:
        print 'Failed to get repo releases on github'
        print response.json()
        sys.exit(1)

    for release in response.json():
        if release['tag_name'] == new_version:
            print 'Version already exists in github'
            sys.exit(1)


    # Build webapp
    subprocess.check_call(['grunt', '--ver=%s' % get_int_ver(new_version)],
        cwd=STYLES_DIR)
    subprocess.check_call(['grunt'], cwd=WWW_DIR)


    # Generate changelog
    debian_changelog = ''
    changelog_version = None
    release_body = ''
    snapshot_lines = []
    if is_snapshot:
        snapshot_lines.append('Version %s %s' % (
            new_version, datetime.datetime.utcnow().strftime('%Y-%m-%d')))
        snapshot_lines.append('Snapshot release')

    with open(CHANGES_PATH, 'r') as changelog_file:
        for line in snapshot_lines + changelog_file.readlines()[2:]:
            line = line.strip()

            if not line or line[0] == '-':
                continue

            if line[:7] == 'Version':
                if debian_changelog:
                    debian_changelog += '\n -- %s <%s>  %s -0400\n\n' % (
                        maintainer,
                        maintainer_email,
                        date.strftime('%a, %d %b %Y %H:%M:%S'),
                    )

                _, version, date = line.split(' ')
                date = datetime.datetime.strptime(date, '%Y-%m-%d')

                if not changelog_version:
                    changelog_version = version

                debian_changelog += \
                    '%s (%s-%subuntu1) unstable; urgency=low\n\n' % (
                    build_num, pkg_name, version)

            elif debian_changelog:
                debian_changelog += '  * %s\n' % line

                if not is_snapshot and version == new_version:
                    release_body += '* %s\n' % line

        debian_changelog += '\n -- %s <%s>  %s -0400\n' % (
            maintainer,
            maintainer_email,
            date.strftime('%a, %d %b %Y %H:%M:%S'),
        )

    if not is_snapshot and changelog_version != new_version:
        print 'New version does not exist in changes'
        sys.exit(1)

    with open(DEBIAN_CHANGELOG_PATH, 'w') as changelog_file:
        changelog_file.write(debian_changelog)

    if not is_snapshot and not release_body:
        print 'Failed to generate github release body'
        sys.exit(1)
    elif is_snapshot:
        release_body = '* Snapshot release'
    release_body = release_body.rstrip('\n')


    # Update arch package
    pkgbuild_path = ARCH_DEV_PKGBUILD if is_snapshot else ARCH_PKGBUILD
    with open(pkgbuild_path, 'r') as pkgbuild_file:
        pkgbuild_data = re.sub(
            'pkgver=(.*)',
            'pkgver=%s' % new_version,
            pkgbuild_file.read(),
        )

    with open(pkgbuild_path, 'w') as pkgbuild_file:
        pkgbuild_file.write(pkgbuild_data)


    # Update centos package
    pkgspec_path = CENTOS_DEV_PKGSPEC if is_snapshot else CENTOS_PKGSPEC
    with open(pkgspec_path, 'r') as pkgspec_file:
        pkgspec_data = re.sub(
            '%define pkgver (.*)',
            '%%define pkgver %s' % new_version,
            pkgspec_file.read(),
        )

    with open(pkgspec_path, 'w') as pkgspec_file:
        pkgspec_file.write(pkgspec_data)


    # Git commit
    subprocess.check_call(['git', 'reset', 'HEAD', '.'])
    subprocess.check_call(['git', 'add', 'debian/changelog'])
    subprocess.check_call(['git', 'add', 'arch/dev/PKGBUILD'])
    subprocess.check_call(['git', 'add', 'arch/git/PKGBUILD'])
    subprocess.check_call(['git', 'add', 'arch/production/PKGBUILD'])
    subprocess.check_call(['git', 'add', 'centos/pritunl.spec'])
    subprocess.check_call(['git', 'add', 'centos/pritunl-dev.spec'])
    subprocess.check_call(['git', 'commit', '-m', 'Create new release'])
    subprocess.check_call(['git', 'push'])


    # Create branch
    subprocess.check_call(['git', 'branch', new_version])
    subprocess.check_call(['git', 'push', '-u', 'origin', new_version])
    time.sleep(8)


    # Create release
    response = requests.post(
        'https://api.github.com/repos/%s/%s/releases' % (
            github_owner, pkg_name),
        headers={
            'Authorization': 'token %s' % github_token,
            'Content-type': 'application/json',
        },
        data=json.dumps({
            'tag_name': new_version,
            'name': '%s v%s' % (pkg_name, new_version),
            'body': release_body,
            'prerelease': is_snapshot,
            'target_commitish': new_version,
        }),
    )

    if response.status_code != 201:
        print 'Failed to create release on github'
        print response.json()
        sys.exit(1)


elif cmd == 'build':
    build_dir = 'build/%s' % cur_version

    passphrase = getpass.getpass('Enter GPG passphrase: ')

    if not os.path.isdir(build_dir):
        os.makedirs(build_dir)

    # Import gpg key
    vagrant_check_call('sudo gpg --import private_key.asc || true',
        cwd='tools')

    # Download archive
    archive_name = '%s.tar.gz' % cur_version
    archive_path = os.path.join(build_dir, archive_name)
    if not os.path.isfile(archive_path):
        wget('https://github.com/pritunl/pritunl/archive/' + archive_name,
            cwd=build_dir)

    # Create orig archive
    orig_name = '%s_%s.orig.tar.gz' % (pkg_name, cur_version)
    orig_path = os.path.join(build_dir, orig_name)
    if not os.path.isfile(orig_path):
        tar_extract(archive_name, cwd=build_dir)
        rm_tree(os.path.join(
            build_dir,
            '%s-%s/debian' % (pkg_name, cur_version),
        ))
        tar_compress(
            orig_name,
            '%s-%s' % (pkg_name, cur_version),
            cwd=build_dir,
        )
        rm_tree(os.path.join(
            build_dir,
            '%s-%s' % (pkg_name, cur_version),
        ))

    # Create build path
    build_name = '%s-%s' % (pkg_name, cur_version)
    build_path = os.path.join(build_dir, build_name)
    if not os.path.isdir(build_path):
        tar_extract(archive_name, cwd=build_dir)

    # Read changelog
    changelog_path = os.path.join(build_path, DEBIAN_CHANGELOG_PATH)
    with open(changelog_path, 'r') as changelog_file:
        changelog_data = changelog_file.read()

    # Build debian packages
    for ubuntu_release in UBUNTU_RELEASES:
        with open(changelog_path, 'w') as changelog_file:
            changelog_file.write(re.sub(
                'ubuntu1(.*);',
                'ubuntu1~%s) %s;' % (ubuntu_release, ubuntu_release),
                changelog_data,
            ))

        vagrant_check_call(
            'sudo debuild -S -p"gpg --no-tty --passphrase %s"' % (
                passphrase),
            cwd=build_path,
        )

else:
    sys.exit(0)
