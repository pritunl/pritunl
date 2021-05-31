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
import zlib
import getpass
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import (
    Cipher, algorithms, modes
)
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

USAGE = """Usage: builder [command] [options]
Command Help: builder [command] --help

Commands:
  version               Print the version and exit
  sync-db               Sync database
  set-version           Set current version
  build                 Build and release
  upload                Upload release
  build-upload          Build and upload release
  upload-github         Upload release to GitHub"""

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
    for i in range(5):
        file_size = os.path.getsize(file_path)
        response = requests.post(
            'https://uploads.github.com/repos/%s/%s/releases/%s/assets' % (
                github_owner, pkg_name, release_id),
            verify=False,
            headers={
                'Authorization': 'token %s' % github_token,
                'Content-Type': 'application/octet-stream',
                'Content-Size': str(file_size),
            },
            params={
                'name': file_name,
            },
            data=open(file_path, 'rb').read(),
        )

        if response.status_code == 201:
            return
        else:
            time.sleep(1)

    data = response.json()
    errors = data.get('errors')
    if not errors or errors[0].get('code') != 'already_exists':
        print('Failed to create asset on github')
        print(data)
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
            if cur_version not in name:
                continue
            elif name.endswith(".pkg.tar.xz"):
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
    import werkzeug.http
    file_name = os.path.basename(file_path).encode(
        sys.getfilesystemencoding())
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
    import pymongo

    releases_dbs = []
    for mongodb_uri in mongodb_uris:
        mongo_client = pymongo.MongoClient(mongodb_uri)
        mongo_db = mongo_client.get_default_database()
        releases_dbs.append(mongo_db.releases)

    for releases_db in releases_dbs:
        for file_name in os.listdir(RELEASES_DIR):
            file_path = os.path.join(RELEASES_DIR, file_name)
            ver, file_type, _ = file_name.split('.')
            if file_type == 'release':
                with open(file_path, 'r') as release_file:
                    doc = json.loads(release_file.read().strip())
                    releases_db.update_one({
                        '_id': ver,
                    }, {
                        '$set': doc,
                    }, upsert=True)
            else:
                last_modified, etag = generate_last_modifited_etag(file_path)
                with open(file_path, 'r') as css_file:
                    releases_db.update_one({
                        '_id': ver,
                    }, {'$set': {
                        file_type: {
                            'etag': etag,
                            'last_modified': last_modified,
                            'data': css_file.read(),
                        },
                    }}, upsert=True)


if len(sys.argv) > 1:
    cmd = sys.argv[1]
else:
    cmd = 'version'

def aes_encrypt(passphrase, data):
    enc_salt = os.urandom(32)
    enc_iv = os.urandom(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA1(),
        length=32,
        salt=enc_salt,
        iterations=1000,
        backend=default_backend(),
    )
    enc_key = kdf.derive(passphrase.encode())

    data += '\x00' * (16 - (len(data) % 16))

    cipher = Cipher(
        algorithms.AES(enc_key),
        modes.CBC(enc_iv),
        backend=default_backend()
    ).encryptor()
    enc_data = cipher.update(data.encode()) + cipher.finalize()

    return '\n'.join([
        base64.b64encode(enc_salt).decode('utf-8'),
        base64.b64encode(enc_iv).decode('utf-8'),
        base64.b64encode(enc_data).decode('utf-8'),
    ])

def aes_decrypt(passphrase, data):
    data = data.split('\n')
    if len(data) < 3:
        raise ValueError('Invalid encryption data')

    enc_salt = base64.b64decode(data[0])
    enc_iv = base64.b64decode(data[1])
    enc_data = base64.b64decode(data[2])

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA1(),
        length=32,
        salt=enc_salt,
        iterations=1000,
        backend=default_backend(),
    )
    enc_key = kdf.derive(passphrase.encode())

    cipher = Cipher(
        algorithms.AES(enc_key),
        modes.CBC(enc_iv),
        backend=default_backend()
    ).decryptor()
    data = cipher.update(enc_data) + cipher.finalize()

    return data.decode('utf-8').replace('\x00', '')

passphrase = getpass.getpass('Enter passphrase: ')

if cmd == 'encrypt':
    passphrase2 = getpass.getpass('Enter passphrase: ')

    if passphrase != passphrase2:
        print('ERROR: Passphrase mismatch')
        sys.exit(1)

    with open(BUILD_KEYS_PATH, 'r') as build_keys_file:
        data = build_keys_file.read().strip()

    enc_data = aes_encrypt(passphrase, data)

    with open(BUILD_KEYS_PATH, 'w') as build_keys_file:
        build_keys_file.write(enc_data)

    sys.exit(0)

if cmd == 'decrypt':
    with open(BUILD_KEYS_PATH, 'r') as build_keys_file:
        enc_data = build_keys_file.read().strip()

    data = aes_decrypt(passphrase, enc_data)

    with open(BUILD_KEYS_PATH, 'w') as build_keys_file:
        build_keys_file.write(data)

    sys.exit(0)

# Load build keys
with open(BUILD_KEYS_PATH, 'r') as build_keys_file:
    enc_data = build_keys_file.read()
    data = aes_decrypt(passphrase, enc_data)
    build_keys = json.loads(data.strip())
    github_owner = build_keys['github_owner']
    github_token = build_keys['github_token']
    gitlab_token = build_keys['gitlab_token']
    gitlab_host = build_keys['gitlab_host']
    mirror_url = build_keys['mirror_url']
    test_mirror_url = build_keys['test_mirror_url']
    mongodb_uris = build_keys['mongodb_uris']

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


parser = optparse.OptionParser(usage=USAGE)
(options, args) = parser.parse_args()

build_num = 0


# Run cmd
if cmd == 'version':
    print('%s v%s' % (app_name, cur_version))
    sys.exit(0)


if cmd == 'sync-db':
    sync_db()


if cmd == 'sync-releases':
    next_url = 'https://api.github.com/repos/%s/%s/releases' % (
        github_owner, pkg_name)

    while True:
        # Get github release
        response = requests.get(
            next_url,
            headers={
                'Authorization': 'token %s' % github_token,
                'Content-type': 'application/json',
            },
        )

        if response.status_code != 200:
            print('Failed to get repo releases on github')
            print(response.json())
            sys.exit(1)

        for release in response.json():
            print(release['tag_name'])

            # Create gitlab release
            resp = requests.post(
                ('https://%s/api/v4/projects' +
                    '/%s%%2F%s/repository/tags/%s/release') % (
                    gitlab_host, github_owner, pkg_name, release['tag_name']),
                headers={
                    'Private-Token': gitlab_token,
                    'Content-type': 'application/json',
                },
                data=json.dumps({
                    'tag_name': release['tag_name'],
                    'description': release['body'],
                }),
            )

            if resp.status_code not in (201, 409):
                print('Failed to create releases on gitlab')
                print(resp.json())
                sys.exit(1)

        if 'Link' not in response.headers or \
                'rel="next"' not in response.headers['Link']:
            break
        next_url = response.headers['Link'].split(';')[0][1:-1]

if cmd == 'set-version':
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
        print('Failed to get repo releases on github')
        print(response.json())
        sys.exit(1)

    for release in response.json():
        if release['tag_name'] == new_version:
            print('Version already exists in github')
            sys.exit(1)


    # Build webapp
    subprocess.check_call([
        'sudo',
        'podman',
        'run',
        '--rm',
        '-ti',
        '-u', 'docker',
        '-v', '%s:/mount:Z' % os.path.join(os.getcwd(), STYLES_DIR),
        'dev',
        'grunt',
        '--ver=%s' % get_int_ver(new_version)
    ])
    subprocess.check_call([
        'sudo',
        'podman',
        'run',
        '--rm',
        '-ti',
        '-u', 'docker',
        '-v', '%s:/mount:Z' % os.path.join(os.getcwd(), WWW_DIR),
        'dev',
        'grunt',
    ])

    css_hash = subprocess.check_output(
        'md5sum www/vendor/dist/css/main.css | head -c 32',
        shell=True).decode().strip()
    app_hash = subprocess.check_output(
        'md5sum www/vendor/dist/js/main.js | head -c 32', shell=True,
    ).decode().strip()
    subprocess.check_call([
        'mv',
        'www/vendor/dist/css/main.css',
        'www/vendor/dist/css/main.%s.css' % css_hash,
    ])
    subprocess.check_call([
        'mv',
        'www/vendor/dist/js/main.js',
        'www/vendor/dist/js/main.%s.js' % app_hash,
    ])
    subprocess.check_call([
        'sed',
        '-i',
        '-e', 's|s/css/main.css|s/css/main.%s.css|g' % css_hash,
        'www/vendor/dist/index.html',
    ])
    subprocess.check_call([
        'sed',
        '-i',
        '-e', 's|s/js/main.js|s/js/main.%s.js|g' % app_hash,
        'www/vendor/dist/index.html',
    ])

    # Commit webapp
    subprocess.check_call(['git', 'reset', 'HEAD', '.'])
    subprocess.check_call(['git', 'add', 'www/styles/vendor/main.css'])
    subprocess.check_call(['git', 'add', '--all', 'www/vendor/dist'])
    changes = subprocess.check_output(
        ['git', 'status', '-s']).decode().rstrip().split('\n')
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
        print('New version does not exist in changes')
        sys.exit(1)

    if is_snapshot:
        release_body = '* Snapshot release'
    elif not release_body:
        print('Failed to generate github release body')
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
    time.sleep(6)


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
        print('Failed to create release on github')
        print(response.json())
        sys.exit(1)

    subprocess.check_call(['git', 'pull'])
    subprocess.check_call(['git', 'push', '--tags'])
    time.sleep(6)


    # Create gitlab release
    response = requests.post(
        ('https://%s/api/v4/projects' +
            '/%s%%2F%s/repository/tags/%s/release') % (
            gitlab_host, github_owner, pkg_name, new_version),
        headers={
            'Private-Token': gitlab_token,
            'Content-type': 'application/json',
        },
        data=json.dumps({
            'tag_name': new_version,
            'description': release_body,
        }),
    )

    if response.status_code != 201:
        print('Failed to create release on gitlab')
        print(response.json())
        sys.exit(1)


if cmd == 'build' or cmd == 'build-upload':
    if len(args) > 1:
        build_version = args[1]
    else:
        build_version = cur_version

    is_snapshot = 'snapshot' in build_version
    pacur_path = TEST_PACUR_PATH if is_snapshot else STABLE_PACUR_PATH


    # Get sha256 sum
    archive_name = '%s.tar.gz' % build_version
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
                'pkgver="%s"' % build_version,
                pkgbuild_file.read(),
            )
            pkgbuild_data = re.sub(
                '"[a-f0-9]{64}"',
                '"%s"' % archive_sha256_sum.decode('utf-8'),
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


if cmd == 'upload' or cmd == 'build-upload':
    if len(args) > 1:
        build_version = args[1]
    else:
        build_version = cur_version

    is_snapshot = 'snapshot' in build_version
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
        if release['tag_name'] == build_version:
            release_id = release['id']

    if not release_id:
        print('Version does not exists in github')
        sys.exit(1)


    # Run pacur project build
    subprocess.check_call(
        ['sudo', 'pacur', 'project', 'repo'],
        cwd=pacur_path,
    )


    # Sync mirror
    subprocess.check_call([
        'mc',
        'mirror',
        '--remove',
        '--overwrite',
        '--md5',
        'mirror',
        'repo-east/unstable',
    ], cwd=pacur_path)

    subprocess.check_call([
        'mc',
        'mirror',
        '--remove',
        '--overwrite',
        '--md5',
        'mirror',
        'repo-west/unstable',
    ], cwd=pacur_path)

    # Add to github
    for name, path in iter_packages():
        post_git_asset(release_id, name, path)


if cmd == 'upload-github':
    if len(args) > 1:
        build_version = args[1]
    else:
        build_version = cur_version

    is_snapshot = 'snapshot' in build_version
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
        if release['tag_name'] == build_version:
            release_id = release['id']

    if not release_id:
        print('Version does not exists in github')
        sys.exit(1)


    # Add to github
    for name, path in iter_packages():
        post_git_asset(release_id, name, path)
