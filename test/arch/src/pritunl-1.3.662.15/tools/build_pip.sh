VERSION=`cat ../pritunl/__init__.py | grep __version__ | cut -d\' -f2`

mkdir -p ../build/pip
cd ../build/pip

wget https://github.com/pritunl/pritunl/archive/$VERSION.tar.gz

mv $VERSION.tar.gz pritunl-$VERSION.tar.gz

cd ../../

python2 setup.py register

echo 'MD5: '`md5sum ./build/pip/pritunl-$VERSION.tar.gz | cut -d' ' -f1`
echo 'UPLOAD: ../build/pip/pritunl-'$VERSION'.tar.gz'
