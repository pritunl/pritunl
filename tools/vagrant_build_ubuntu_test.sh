VERSION=`cat ../pritunl/__init__.py | grep __version__ | cut -d\' -f2`

gpg --import private_key.asc

mkdir -p /vagrant/build/debian_test
cd /vagrant/build/debian_test

wget https://github.com/pritunl/pritunl/archive/master.tar.gz

tar xfz master.tar.gz
mv pritunl-master pritunl-$VERSION
tar cfz $VERSION.tar.gz pritunl-$VERSION

tar xfz $VERSION.tar.gz
rm -rf pritunl-$VERSION/debian
tar cfz pritunl_$VERSION.orig.tar.gz pritunl-$VERSION
rm -rf pritunl-$VERSION

tar xfz $VERSION.tar.gz
cd pritunl-$VERSION

debuild
