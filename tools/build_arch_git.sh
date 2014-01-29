VERSION=`cat ../pritunl/__init__.py | grep __version__ | cut -d\' -f2`

mkdir -p ../build/arch_linux_git
cd ../build/arch_linux_git

cp ../../arch/git/PKGBUILD ./
cp ../../arch/git/pritunl.install ./

makepkg --source
