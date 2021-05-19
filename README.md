# pritunl: enterprise vpn server

[![github](https://img.shields.io/badge/github-pritunl-11bdc2.svg?style=flat)](https://github.com/pritunl)
[![twitter](https://img.shields.io/badge/twitter-pritunl-55acee.svg?style=flat)](https://twitter.com/pritunl)

[Pritunl](https://github.com/pritunl/pritunl) is a distributed enterprise
vpn server built using the OpenVPN protocol. Documentation and more
information can be found at the home page [pritunl.com](https://pritunl.com)

[![pritunl](www/img/logo_code.png)](https://pritunl.com)

## Install From Source

```bash
# Install MongoDB if running single host configuration
sudo tee /etc/yum.repos.d/mongodb-org-4.4.repo << EOF
[mongodb-org-4.4]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/8/mongodb-org/4.4/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-4.4.asc
EOF

sudo yum -y install mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod

# Set current pritunl version X.XX.XXXX.XX
# Set to master to run code from repository (only for testing)
export VERSION="master"

# RHEL EPEL
sudo yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
# Oracle Linux EPEL
sudo yum -y install oracle-epel-release-el8

sudo yum -y install python3-pip python3-devel gcc git openvpn openssl net-tools iptables psmisc ca-certificates selinux-policy selinux-policy-devel python3-virtualenv wget tar

wget https://golang.org/dl/go1.16.4.linux-amd64.tar.gz
echo "7154e88f5a8047aad4b80ebace58a059e36e7e2e4eb3b383127a28c711b4ff59 go1.16.4.linux-amd64.tar.gz" | sha256sum -c -

sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xf go1.16.4.linux-amd64.tar.gz
rm -f go1.16.4.linux-amd64.tar.gz
tee -a ~/.bashrc << EOF
export GO111MODULE=off
export GOPATH=\$HOME/go
export PATH=/usr/local/go/bin:\$PATH
EOF
source ~/.bashrc

sudo systemctl stop pritunl || true
sudo rm -rf /usr/lib/pritunl

sudo mkdir -p /usr/lib/pritunl
sudo mkdir -p /var/lib/pritunl
sudo virtualenv-3 /usr/lib/pritunl

go get -v -u github.com/pritunl/pritunl-dns
go get -v -u github.com/pritunl/pritunl-web
sudo cp -f ~/go/bin/pritunl-dns /usr/bin/pritunl-dns
sudo cp -f ~/go/bin/pritunl-web /usr/bin/pritunl-web

wget https://github.com/pritunl/pritunl/archive/$VERSION.tar.gz
tar xf $VERSION.tar.gz
rm $VERSION.tar.gz
cd ./pritunl-master
/usr/lib/pritunl/bin/python setup.py build
sudo /usr/lib/pritunl/bin/pip3 install -U -r requirements.txt
sudo /usr/lib/pritunl/bin/python setup.py install
sudo ln -sf /usr/lib/pritunl/bin/pritunl /usr/bin/pritunl

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
sudo restorecon -v /usr/lib/pritunl/bin/pritunl || true
sudo restorecon -v /usr/lib/pritunl/bin/python || true
sudo restorecon -v /usr/lib/pritunl/bin/python3 || true
sudo restorecon -v /usr/lib/pritunl/bin/python3.6 || true
sudo restorecon -v /usr/bin/pritunl-web || true
sudo restorecon -v /usr/bin/pritunl-dns || true
sudo restorecon -v -R /var/lib/pritunl || true
sudo restorecon -v /var/log/pritunl* || true

cd ../../
sudo rm -rf ./pritunl-master

sudo systemctl daemon-reload
sudo systemctl start pritunl
sudo systemctl enable pritunl
```

## License

Please refer to the [`LICENSE`](LICENSE) file for a copy of the license.
