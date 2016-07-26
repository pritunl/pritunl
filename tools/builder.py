import optparse
import datetime
import re
import sys
import json
import os
import subprocess
import time
import math
import requests
import pymongo
import zlib
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
STABLE_PACUR_PATH = '../pritunl-pacur'
TEST_PACUR_PATH = '../pritunl-pacur-test'
BUILD_TARGETS = ('pritunl',)
WWW_DIR = 'www'
STYLES_DIR = 'www/styles'
RELEASES_DIR = 'www/styles/releases'

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
cur_date = datetime.datetime.utcnow()
pacur_path = None

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
        data = response.json()
        errors = data.get('errors')
        if not errors or errors[0].get('code') != 'already_exists':
            print 'Failed to create asset on github'
            print data
            sys.exit(1)

def get_ver(version):
    day_num = (cur_date - datetime.datetime(2013, 9, 12)).days
    min_num = int(math.floor(((cur_date.hour * 60) + cur_date.minute) / 14.4))
    ver = re.findall(r'\d+', version)
    ver_str = '.'.join((ver[0], ver[1], str(day_num), str(min_num)))
    ver_str += ''.join(re.findall('[a-z]+', version))

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
        ver[-1] = str(int(ver[-1]) + 4000)

    return int(''.join([x.zfill(4) for x in ver]))

def iter_packages():
    for target in BUILD_TARGETS:
        target_path = os.path.join(pacur_path, target)
        for name in os.listdir(target_path):
            if name.endswith(".pkg.tar.xz"):
                pass
            elif name.endswith(".rpm"):
                pass
            elif name.endswith(".deb"):
                pass
            else:
                continue

            path = os.path.join(target_path, name)

            yield name, path

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
    mirror_url = build_keys['mirror_url']
    test_mirror_url = build_keys['test_mirror_url']
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
(options, args) = parser.parse_args()

build_num = 0


# Run cmd
if cmd == 'version':
    print '%s v%s' % (app_name, cur_version)
    sys.exit(0)


elif cmd == 'sync-db':
    sync_db()


elif cmd == 'set-version':
    new_version_orig = args[1]
    new_version = get_ver(new_version_orig)
    is_snapshot = 'snapshot' in new_version
    pacur_path = TEST_PACUR_PATH if is_snapshot else STABLE_PACUR_PATH


    # Update changes
    if not is_snapshot:
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
    subprocess.check_call([
        'docker',
        'run',
        '--rm',
        '-ti',
        '-v', '%s:/mount' % os.path.join(os.getcwd(), STYLES_DIR),
        'npm',
        'grunt',
        '--ver=%s' % get_int_ver(new_version)
    ])
    subprocess.check_call([
        'docker',
        'run',
        '--rm',
        '-ti',
        '-v', '%s:/mount' % os.path.join(os.getcwd(), WWW_DIR),
        'npm',
        'grunt',
    ])

    # Commit webapp
    subprocess.check_call(['git', 'reset', 'HEAD', '.'])
    subprocess.check_call(['git', 'add', 'www/styles/vendor/main.css'])
    subprocess.check_call(['git', 'add', '--all', 'www/vendor/dist'])
    changes = subprocess.check_output(
        ['git', 'status', '-s']).rstrip().split('\n')
    changed = any([True if x[0] == 'M' else False for x in changes])
    if changed:
        subprocess.check_call(['git', 'commit', '-S', '-m', 'Rebuild dist'])
        subprocess.check_call(['git', 'push'])


    # Sync db
    sync_db()


    # Generate changelog
    version = None
    release_body = ''
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

    if is_snapshot:
        release_body = '* Snapshot release'
    elif not release_body:
        print 'Failed to generate github release body'
        sys.exit(1)
    release_body = release_body.rstrip('\n')


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
    subprocess.check_call(['git', 'commit', '-S', '-m', 'Create new release'])
    subprocess.check_call(['git', 'push'])


    # Create branch
    if not is_snapshot:
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
            'target_commitish': 'master' if is_snapshot else new_version,
        }),
    )

    if response.status_code != 201:
        print 'Failed to create release on github'
        print response.json()
        sys.exit(1)

    subprocess.check_call(['git', 'pull'])
    subprocess.check_call(['git', 'push', '--tags'])


elif cmd == 'build':
    is_snapshot = 'snapshot' in cur_version
    pacur_path = TEST_PACUR_PATH if is_snapshot else STABLE_PACUR_PATH


    # Get sha256 sum
    archive_name = '%s.tar.gz' % cur_version
    archive_path = os.path.join(os.path.sep, 'tmp', archive_name)
    if os.path.isfile(archive_path):
        os.remove(archive_path)
    wget('https://github.com/%s/%s/archive/%s' % (
        github_owner, pkg_name, archive_name),
        output=archive_name,
        cwd=os.path.join(os.path.sep, 'tmp'),
    )
    archive_sha256_sum = subprocess.check_output(
        ['sha256sum', archive_path]).split()[0]
    os.remove(archive_path)


    # Update sha256 sum and pkgver in PKGBUILD
    for target in BUILD_TARGETS:
        pkgbuild_path = os.path.join(pacur_path, target, 'PKGBUILD')

        with open(pkgbuild_path, 'r') as pkgbuild_file:
            pkgbuild_data = re.sub(
                'pkgver="(.*)"',
                'pkgver="%s"' % cur_version,
                pkgbuild_file.read(),
            )
            pkgbuild_data = re.sub(
                '"[a-f0-9]{64}"',
                '"%s"' % archive_sha256_sum,
                pkgbuild_data,
            )

        with open(pkgbuild_path, 'w') as pkgbuild_file:
            pkgbuild_file.write(pkgbuild_data)


    # Run pacur project build
    for build_target in BUILD_TARGETS:
        subprocess.check_call(
            ['sudo', 'pacur', 'project', 'build', build_target],
            cwd=pacur_path,
        )


elif cmd == 'upload':
    is_snapshot = 'snapshot' in cur_version
    pacur_path = TEST_PACUR_PATH if is_snapshot else STABLE_PACUR_PATH


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


    # Run pacur project build
    subprocess.check_call(
        ['sudo', 'pacur', 'project', 'repo'],
        cwd=pacur_path,
    )


    # Sync mirror
    for mir_url in test_mirror_url if is_snapshot else mirror_url:
        subprocess.check_call(['rsync',
            '--human-readable',
            '--archive',
            '--progress',
            '--delete',
            '--acls',
            'mirror/',
            mir_url,
        ], cwd=pacur_path)


    # Add to github
    for name, path in iter_packages():
        post_git_asset(release_id, name, path)


elif cmd == 'upload-github':
    is_snapshot = 'snapshot' in cur_version
    pacur_path = TEST_PACUR_PATH if is_snapshot else STABLE_PACUR_PATH


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


    # Add to github
    for name, path in iter_packages():
        post_git_asset(release_id, name, path)

else:
    print 'Unknown command'
    sys.exit(1)
