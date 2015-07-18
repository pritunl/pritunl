import optparse
import datetime
import re
import sys
import json
import os
import subprocess
import time
import getpass
import zlib
import math
import pymongo
import requests
import werkzeug.http

USAGE = """Usage: builder [command] [options]
Command Help: builder [command] --help

Commands:
  version               Print the version and exit
  sync-db               Sync database
  set-version           Set current version
  build                 Build and release"""

INIT_PATH = 'pritunl/__init__.py'
SETUP_PATH = 'setup.py'
CHANGES_PATH = 'CHANGES'
BUILD_KEYS_PATH = 'tools/build_keys.json'
ARCH_PKGBUILD_PATH = 'arch/production/PKGBUILD'
ARCH_DEV_PKGBUILD_PATH = 'arch/dev/PKGBUILD'
ARCH_PKGINSTALL = 'arch/production/pritunl.install'
ARCH_DEV_PKGINSTALL = 'arch/dev/pritunl.install'
CENTOS_PKGSPEC_PATH = 'centos/pritunl.spec'
CENTOS_DEV_PKGSPEC_PATH = 'centos/pritunl-dev.spec'
WWW_DIR = 'www'
STYLES_DIR = 'www/styles'
RELEASES_DIR = 'www/styles/releases'
AUR_CATEGORY = 13

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
cur_date = datetime.datetime.utcnow()

def vagrant_popen(cmd, cwd=None, name='centos'):
    if cwd:
        cmd = 'cd /vagrant/%s; %s' % (cwd, cmd)
    return subprocess.Popen("vagrant ssh --command='%s' %s" % (cmd, name),
        shell=True, stdin=subprocess.PIPE)

def vagrant_check_call(cmd, cwd=None, name='debian'):
    if cwd:
        cmd = 'cd /vagrant/%s; %s' % (cwd, cmd)
    return subprocess.check_call("vagrant ssh --command='%s' %s" % (cmd, name),
        shell=True, stdin=subprocess.PIPE)

def wget(url, cwd=None, output=None):
    if output:
        args = ['wget', '-O', output, url]
    else:
        args = ['wget', url]
    subprocess.check_call(args, cwd=cwd)

def post_git_asset(release_id, file_name, file_path):
    file_size = os.path.getsize(file_path)
    response = requests.post(
        'https://uploads.github.com/repos/%s/%s/releases/%s/assets' % (
            github_owner, pkg_name, release_id),
        verify=False,
        headers={
            'Authorization': 'token %s' % github_token,
            'Content-Type': 'application/octet-stream',
            'Content-Size': file_size,
        },
        params={
            'name': file_name,
        },
        data=open(file_path, 'rb').read(),
    )

    if response.status_code != 201:
        print 'Failed to create release on github'
        print response.json()
        sys.exit(1)

def rm_tree(path):
    subprocess.check_call(['rm', '-rf', path])

def tar_extract(archive_path, cwd=None):
    subprocess.check_call(['tar', 'xfz', archive_path], cwd=cwd)

def tar_compress(archive_path, in_path, cwd=None):
    subprocess.check_call(['tar', 'cfz', archive_path, in_path], cwd=cwd)

def get_ver(version):
    day_num = (cur_date - datetime.datetime(2013, 9, 12)).days
    min_num = int(math.floor(((cur_date.hour * 60) + cur_date.minute) / 14.4))
    ver = re.findall(r'\d+', version)
    ver_str = '.'.join((ver[0], ver[1], str(day_num), str(min_num)))

    name = ''.join(re.findall('[a-z]+', version))
    if name:
        ver_str += name + ver[2]

    return ver_str

def get_int_ver(version):
    ver = re.findall(r'\d+', version)

    if 'snapshot' in version:
        pass
    elif 'alpha' in version:
        ver[-1] = str(int(ver[-1]) + 1000)
    elif 'beta' in version:
        ver[-1] = str(int(ver[-1]) + 2000)
    elif 'rc' in version:
        ver[-1] = str(int(ver[-1]) + 3000)
    else:
        ver.append('4000')

    return int(''.join([x.zfill(4) for x in ver]))

def generate_last_modifited_etag(file_path):
    file_name = os.path.basename(file_path).encode(sys.getfilesystemencoding())
    file_mtime = datetime.datetime.utcfromtimestamp(
        os.path.getmtime(file_path))
    file_size = int(os.path.getsize(file_path))
    last_modified = werkzeug.http.http_date(file_mtime)

    return (last_modified, 'wzsdm-%d-%s-%s' % (
        time.mktime(file_mtime.timetuple()),
        file_size,
        zlib.adler32(file_name) & 0xffffffff,
    ))

def sync_db():
    for releases_db in releases_dbs:
        for file_name in os.listdir(RELEASES_DIR):
            file_path = os.path.join(RELEASES_DIR, file_name)
            ver, file_type, _ = file_name.split('.')
            if file_type == 'release':
                with open(file_path, 'r') as release_file:
                    doc = json.loads(release_file.read().strip())
                    releases_db.update({
                        '_id': ver,
                    }, {
                        '$set': doc,
                    }, upsert=True)
            else:
                last_modified, etag = generate_last_modifited_etag(file_path)
                with open(file_path, 'r') as css_file:
                    releases_db.update({
                        '_id': ver,
                    }, {'$set': {
                        file_type: {
                            'etag': etag,
                            'last_modified': last_modified,
                            'data': css_file.read(),
                        },
                    }}, upsert=True)


# Load build keys
with open(BUILD_KEYS_PATH, 'r') as build_keys_file:
    build_keys = json.loads(build_keys_file.read().strip())
    github_owner = build_keys['github_owner']
    github_token = build_keys['github_token']
    aur_username = build_keys['aur_username']
    aur_password = build_keys['aur_password']
    mongodb_uris = build_keys['mongodb_uris']

releases_dbs = []
for mongodb_uri in mongodb_uris:
    mongo_client = pymongo.MongoClient(mongodb_uri)
    mongo_db = mongo_client.get_default_database()
    releases_dbs.append(mongo_db.releases)

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

parser.add_option('--test', action='store_true',
    help='Upload to test repo')

(options, args) = parser.parse_args()

build_num = 0

if cmd == 'version':
    print '%s v%s' % (app_name, cur_version)
    sys.exit(0)


elif cmd == 'sync-db':
    sync_db()


elif cmd == 'set-version':
    new_version_orig = args[1]
    new_version = get_ver(new_version_orig)

    is_snapshot = 'snapshot' in new_version
    is_dev_release = any((
        'snapshot' in new_version,
        'alpha' in new_version,
        'beta' in new_version,
        'rc' in new_version,
    ))


    # Update changes
    with open(CHANGES_PATH, 'r') as changes_file:
        changes_data = changes_file.read()

    with open(CHANGES_PATH, 'w') as changes_file:
        ver_date_str = 'Version ' + new_version.replace(
            'v', '') + cur_date.strftime(' %Y-%m-%d')
        changes_file.write(changes_data.replace(
            '<%= version %>',
            '%s\n%s' % (ver_date_str, '-' * len(ver_date_str)),
        ))


    # Check for duplicate version
    response = requests.get(
        'https://api.github.com/repos/%s/%s/releases' % (
            github_owner, pkg_name),
        headers={
            'Authorization': 'token %s' % github_token,
            'Content-type': 'application/json',
        },
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


    # Commit webapp
    subprocess.check_call(['git', 'reset', 'HEAD', '.'])
    subprocess.check_call(['git', 'add', 'www/styles/vendor/main.css'])
    subprocess.check_call(['git', 'add', '--all', 'www/vendor/dist'])
    changes = subprocess.check_output(
        ['git', 'status', '-s']).rstrip().split('\n')
    changed = any([True if x[0] == 'M' else False for x in changes])
    if changed:
        subprocess.check_call(['git', 'commit', '-m', 'Rebuild dist'])
        subprocess.check_call(['git', 'push'])


    # Sync db
    sync_db()


    # Generate changelog
    version = None
    release_body = ''
    snapshot_lines = []
    if not is_snapshot:
        with open(CHANGES_PATH, 'r') as changelog_file:
            for line in changelog_file.readlines()[2:]:
                line = line.strip()

                if not line or line[0] == '-':
                    continue

                if line[:7] == 'Version':
                    if version:
                        break
                    version = line.split(' ')[1]
                elif version:
                    release_body += '* %s\n' % line

    if not is_snapshot and version != new_version:
        print 'New version does not exist in changes'
        sys.exit(1)

    if not is_snapshot and not release_body:
        print 'Failed to generate github release body'
        sys.exit(1)
    elif is_snapshot:
        release_body = '* Snapshot release'
    release_body = release_body.rstrip('\n')


    # Update arch package
    pkgbuild_path = ARCH_DEV_PKGBUILD_PATH if is_dev_release else \
        ARCH_PKGBUILD_PATH
    with open(pkgbuild_path, 'r') as pkgbuild_file:
        pkgbuild_data = re.sub(
            'pkgver=(.*)',
            'pkgver=%s' % new_version,
            pkgbuild_file.read(),
        )
        pkgbuild_data = re.sub(
            'pkgrel=(.*)',
            'pkgrel=%s' % (build_num + 1),
            pkgbuild_data,
        )

    with open(pkgbuild_path, 'w') as pkgbuild_file:
        pkgbuild_file.write(pkgbuild_data)


    # Update centos package
    pkgspec_path = CENTOS_DEV_PKGSPEC_PATH if is_dev_release else \
        CENTOS_PKGSPEC_PATH
    with open(pkgspec_path, 'r') as pkgspec_file:
        pkgspec_data = re.sub(
            '%define pkgver (.*)',
            '%%define pkgver %s' % new_version,
            pkgspec_file.read(),
        )
        pkgspec_data = re.sub(
            '%define pkgrelease (.*)',
            '%%define pkgrelease %s' % (build_num + 1),
            pkgspec_data,
        )

    with open(pkgspec_path, 'w') as pkgspec_file:
        pkgspec_file.write(pkgspec_data)


    # Update init
    with open(INIT_PATH, 'r') as init_file:
        init_data = init_file.read()

    with open(INIT_PATH, 'w') as init_file:
        init_file.write(re.sub(
            "(__version__ = )('.*?')",
            "__version__ = '%s'" % new_version,
            init_data,
        ))


    # Update setup
    with open(SETUP_PATH, 'r') as setup_file:
        setup_data = setup_file.read()

    with open(SETUP_PATH, 'w') as setup_file:
        setup_file.write(re.sub(
            "(VERSION = )('.*?')",
            "VERSION = '%s'" % new_version,
            setup_data,
        ))


    # Git commit
    subprocess.check_call(['git', 'reset', 'HEAD', '.'])
    subprocess.check_call(['git', 'add', CHANGES_PATH])
    subprocess.check_call(['git', 'add', INIT_PATH])
    subprocess.check_call(['git', 'add', SETUP_PATH])
    subprocess.check_call(['git', 'add', ARCH_PKGBUILD_PATH])
    subprocess.check_call(['git', 'add', ARCH_DEV_PKGBUILD_PATH])
    subprocess.check_call(['git', 'add', CENTOS_PKGSPEC_PATH])
    subprocess.check_call(['git', 'add', CENTOS_DEV_PKGSPEC_PATH])
    subprocess.check_call(['git', 'commit', '-m', 'Create new release'])
    subprocess.check_call(['git', 'push'])


    # Create branch
    if not is_dev_release:
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
            'prerelease': is_dev_release,
            'target_commitish': 'master' if is_dev_release else new_version,
        }),
    )

    if response.status_code != 201:
        print 'Failed to create release on github'
        print response.json()
        sys.exit(1)


elif cmd == 'build':
    is_dev_release = any((
        'snapshot' in cur_version,
        'alpha' in cur_version,
        'beta' in cur_version,
        'rc' in cur_version,
    ))


    # Start vagrant boxes
    subprocess.check_call(['vagrant', 'up', 'centos'])


    # Create arch package
    build_dir = 'build/%s/arch' % cur_version

    if not os.path.isdir(build_dir):
        os.makedirs(build_dir)


    # Download archive
    archive_name = '%s.tar.gz' % cur_version
    archive_path = os.path.join(build_dir, archive_name)
    if not os.path.isfile(archive_path):
        wget('https://github.com/%s/%s/archive/%s' % (
                github_owner, pkg_name, archive_name),
            output=archive_name,
            cwd=build_dir,
        )


    # Get sha256 sum
    archive_sha256_sum = subprocess.check_output(
        ['sha256sum', archive_path]).split()[0]


    # Generate pkgbuild
    pkgbuild_path = ARCH_DEV_PKGBUILD_PATH if is_dev_release else \
        ARCH_PKGBUILD_PATH
    with open(pkgbuild_path, 'r') as pkgbuild_file:
        pkgbuild_data = pkgbuild_file.read()
    pkgbuild_data = pkgbuild_data.replace('CHANGE_ME', archive_sha256_sum)

    pkgbuild_path = os.path.join(build_dir, 'PKGBUILD')
    with open(pkgbuild_path, 'w') as pkgbuild_file:
         pkgbuild_file.write(pkgbuild_data)

    pkginstall_path = ARCH_DEV_PKGINSTALL if is_dev_release else \
        ARCH_PKGINSTALL
    subprocess.check_call(['cp', pkginstall_path, build_dir])


    # Build arch package
    subprocess.check_call(['makepkg', '-f'], cwd=build_dir)
    subprocess.check_call(['mkaurball', '-f'], cwd=build_dir)


    # Create centos package
    build_dir = 'build/%s/centos' % cur_version

    if not os.path.isdir(build_dir):
        os.makedirs(build_dir)


    # Create rpm dirs
    rpm_build_path = os.path.join(build_dir, 'BUILD')
    rpm_rpms_path = os.path.join(build_dir, 'RPMS')
    rpm_sources_path = os.path.join(build_dir, 'SOURCES')
    rpm_specs_path = os.path.join(build_dir, 'SPECS')
    rpm_srpms_path = os.path.join(build_dir, 'SRPMS')

    for rpm_dir_path in (
                rpm_build_path,
                rpm_rpms_path,
                rpm_sources_path,
                rpm_specs_path,
                rpm_srpms_path,
            ):
        if not os.path.isdir(rpm_dir_path):
            os.makedirs(rpm_dir_path)


    # Download archive
    archive_name = '%s.tar.gz' % cur_version
    archive_path = os.path.join(build_dir, archive_name)
    if not os.path.isfile(archive_path):
        wget('https://github.com/%s/%s/archive/%s' % (
                github_owner, pkg_name, archive_name),
            output=archive_name,
            cwd=build_dir,
        )

        tar_extract(archive_name, build_dir)


    # Create rpm spec
    rpm_spec_name = 'pritunl%s.spec' % ('-dev' if is_dev_release else '')
    rpm_spec_path = os.path.join(rpm_specs_path, rpm_spec_name)
    rpm_source_spec_path = os.path.join(build_dir, '%s-%s' % (
        pkg_name, cur_version), 'centos', rpm_spec_name)

    subprocess.check_call(['cp', rpm_source_spec_path, rpm_spec_path])


    # Fix rpm script hardlinking when hardlinks not supported
    vagrant_check_call(
        'sudo sed -i -e "s/ln /cp /g" /usr/lib/rpm/redhat/brp-python-hardlink',
        name='centos',
    )


    # Build rpm spec
    topdir_path = os.path.join('/vagrant', build_dir)
    vagrant_check_call('rpmbuild --define "_topdir %s" -ba %s' % (
        topdir_path, rpm_spec_name), name='centos',
        cwd=rpm_specs_path)


elif cmd == 'upload':
    is_dev_release = any((
        'snapshot' in cur_version,
        'alpha' in cur_version,
        'beta' in cur_version,
        'rc' in cur_version,
    ))


    # Get release id
    release_id = None
    response = requests.get(
        'https://api.github.com/repos/%s/%s/releases' % (
            github_owner, pkg_name),
        headers={
            'Authorization': 'token %s' % github_token,
            'Content-type': 'application/json',
        },
    )

    for release in response.json():
        if release['tag_name'] == cur_version:
            release_id = release['id']

    if not release_id:
        print 'Version does not exists in github'
        sys.exit(1)


    # Upload arch package
    build_dir = 'build/%s/arch' % cur_version
    aur_pkg_name = '%s-%s-%s-any.pkg.tar.xz' % (
        pkg_name + '-dev' if is_dev_release else pkg_name,
        cur_version,
        build_num + 1,
    )
    aur_path = os.path.join(build_dir, aur_pkg_name)
    aurball_pkg_name = '%s-%s-%s.src.tar.gz' % (
        pkg_name + '-dev' if is_dev_release else pkg_name,
        cur_version,
        build_num + 1,
    )
    aurball_path = os.path.join(build_dir, aurball_pkg_name)

    post_git_asset(release_id, aur_pkg_name, aur_path)


    # Upload centos package
    rpms_dir = 'build/%s/centos/RPMS/x86_64' % cur_version
    rpm_name = '%s-%s-%s.el7.centos.x86_64.rpm' % (
        pkg_name + '-dev' if is_dev_release else pkg_name,
        cur_version,
        build_num + 1,
    )
    rpm_path = os.path.join(rpms_dir, rpm_name)

    post_git_asset(release_id, rpm_name, rpm_path)


else:
    print 'Unknown command'
    sys.exit(1)
