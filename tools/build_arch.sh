VERSION=`cat ../pritunl/__init__.py | grep __version__ | cut -d\' -f2`

mkdir -p ../build/arch_linux
cd ../build/arch_linux

wget https://github.com/pritunl/pritunl/archive/$VERSION.tar.gz

cp ../../arch/production/PKGBUILD ./
cp ../../arch/production/pritunl.install ./

TAR_SHA256=$(sha256sum $VERSION.tar.gz | cut -d' ' -f1)
sed -i -e 's/CHANGE_ME/'$TAR_SHA256'/g' PKGBUILD

makepkg --source
