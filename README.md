# pritunl: enterprise vpn server

[![github](https://img.shields.io/badge/github-pritunl-11bdc2.svg?style=flat)](https://github.com/pritunl)
[![twitter](https://img.shields.io/badge/twitter-pritunl-55acee.svg?style=flat)](https://twitter.com/pritunl)
[![medium](https://img.shields.io/badge/medium-pritunl-b32b2b.svg?style=flat)](https://pritunl.medium.com)
[![forum](https://img.shields.io/badge/discussion-forum-ffffff.svg?style=flat)](https://forum.pritunl.com)

[Pritunl](https://github.com/pritunl/pritunl) is a distributed enterprise
vpn server built using the OpenVPN protocol. Documentation and more
information can be found at the home page [pritunl.com](https://pritunl.com)

[![pritunl](www/img/logo_code.png)](https://pritunl.com)

## Install From Source

```bash
# Install MongoDB if running single host configuration
sudo tee /etc/yum.repos.d/mongodb-org.repo << EOF
[mongodb-org-8.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/9/mongodb-org/8.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-8.0.asc
EOF

sudo yum -y install mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod

# Set current pritunl version X.XX.XXXX.XX
# Set to master to run code from repository (only for testing)
export VERSION="master"

# RHEL EPEL
sudo yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm
# Oracle Linux EPEL
sudo yum -y install oracle-epel-release-el9
sudo yum-config-manager --enable ol9_developer_EPEL

sudo yum -y install openssl-devel bzip2-devel libffi-devel sqlite-devel xz-devel zlib-devel gcc git openvpn openssl net-tools iptables psmisc ca-certificates selinux-policy selinux-policy-devel wget tar policycoreutils-python-utils

wget https://www.python.org/ftp/python/3.9.20/Python-3.9.20.tar.xz
echo "6b281279efd85294d2d6993e173983a57464c0133956fbbb5536ec9646beaf0c Python-3.9.20.tar.xz" | sha256sum -c -

tar xf Python-3.9.20.tar.xz
cd ./Python-3.9.20
mkdir /usr/lib/pritunl
./configure --prefix=/usr --libdir=/usr/lib --enable-optimizations --enable-ipv6 --enable-loadable-sqlite-extensions --disable-shared --with-lto --with-platlibdir=lib
make DESTDIR="/usr/lib/pritunl" install
/usr/lib/pritunl/usr/bin/python3 -m ensurepip --upgrade
/usr/lib/pritunl/usr/bin/python3 -m pip install --upgrade pip

wget https://go.dev/dl/go1.23.6.linux-amd64.tar.gz
echo "9379441ea310de000f33a4dc767bd966e72ab2826270e038e78b2c53c2e7802d go1.23.6.linux-amd64.tar.gz" | sha256sum -c -

sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xf go1.23.6.linux-amd64.tar.gz
rm -f go1.23.6.linux-amd64.tar.gz

tee -a ~/.bashrc << EOF
export GOPATH=\$HOME/go
export PATH=/usr/local/go/bin:\$PATH
EOF
source ~/.bashrc

sudo systemctl stop pritunl || true
sudo rm -rf /usr/lib/pritunl

sudo mkdir -p /usr/lib/pritunl
sudo mkdir -p /var/lib/pritunl
sudo virtualenv-3 /usr/lib/pritunl

GOPROXY=direct go install github.com/pritunl/pritunl-web@latest
GOPROXY=direct go install github.com/pritunl/pritunl-dns@latest
sudo rm /usr/bin/pritunl-dns
sudo rm /usr/bin/pritunl-web
sudo cp -f ~/go/bin/pritunl-dns /usr/bin/pritunl-dns
sudo cp -f ~/go/bin/pritunl-web /usr/bin/pritunl-web

go get -v -u github.com/pritunl/pritunl-dns
go get -v -u github.com/pritunl/pritunl-web
sudo cp -f ~/go/bin/pritunl-dns /usr/bin/pritunl-dns
sudo cp -f ~/go/bin/pritunl-web /usr/bin/pritunl-web

wget https://github.com/pritunl/pritunl/archive/$VERSION.tar.gz
tar xf $VERSION.tar.gz
rm $VERSION.tar.gz
cd ./pritunl-$VERSION
/usr/lib/pritunl/bin/python setup.py build
sudo /usr/lib/pritunl/usr/bin/pip3 install --require-hashes -r requirements.txt
sudo /usr/lib/pritunl/usr/bin/python3 setup.py install
sudo ln -sf /usr/lib/pritunl/usr/bin/pritunl /usr/bin/pritunl

cd selinux8
ln -s /usr/share/selinux/devel/Makefile
make
sudo make load
sudo cp pritunl.pp /usr/share/selinux/packages/pritunl.pp
sudo cp pritunl_dns.pp /usr/share/selinux/packages/pritunl_dns.pp
sudo cp pritunl_web.pp /usr/share/selinux/packages/pritunl_web.pp

sudo semodule -i /usr/share/selinux/packages/pritunl.pp /usr/share/selinux/packages/pritunl_dns.pp /usr/share/selinux/packages/pritunl_web.pp
sudo restorecon -v -R /tmp/pritunl* || true
sudo restorecon -v -R /run/pritunl* || true
sudo restorecon -v /etc/systemd/system/pritunl.service || true
sudo restorecon -v /usr/lib/systemd/system/pritunl.service || true
sudo restorecon -v /etc/systemd/system/pritunl-web.service || true
sudo restorecon -v /usr/lib/systemd/system/pritunl-web.service || true
sudo restorecon -v /usr/lib/pritunl/bin/pritunl || true
sudo restorecon -v /usr/lib/pritunl/bin/python || true
sudo restorecon -v /usr/lib/pritunl/bin/python3 || true
sudo restorecon -v /usr/lib/pritunl/bin/python3.6 || true
sudo restorecon -v /usr/lib/pritunl/bin/python3.9 || true
sudo restorecon -v /usr/lib/pritunl/usr/bin/pritunl || true
sudo restorecon -v /usr/lib/pritunl/usr/bin/python || true
sudo restorecon -v /usr/lib/pritunl/usr/bin/python3 || true
sudo restorecon -v /usr/lib/pritunl/usr/bin/python3.6 || true
sudo restorecon -v /usr/lib/pritunl/usr/bin/python3.9 || true
sudo restorecon -v /usr/bin/pritunl-web || true
sudo restorecon -v /usr/bin/pritunl-dns || true
sudo restorecon -v -R /var/lib/pritunl || true
sudo restorecon -v /var/log/pritunl* || true

sudo groupadd -r pritunl-web || true
sudo useradd -r -g pritunl-web -s /sbin/nologin -c 'Pritunl web server' pritunl-web || true

cd ../../
sudo rm -rf ./pritunl-$VERSION

sudo systemctl daemon-reload
sudo systemctl start pritunl
sudo systemctl enable pritunl
```

## License

Please refer to the [`LICENSE`](LICENSE) file for a copy of the license.
