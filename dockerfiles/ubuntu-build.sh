!# /bin/bash
# Install MongoDB if running single host configuration

sudo apt install -y mongodb
sudo systemctl start mongodb
sudo systemctl enable mongodb

# Set current pritunl version X.XX.XXXX.XX
# Set to master to run code from repository (only for testing)
export VERSION="master"

# RHEL EPEL
## sudo yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
# Oracle Linux EPEL
## sudo yum -y install oracle-epel-release-el8

sudo apt install -y python3-pip python3-dev gcc git openvpn openssl net-tools iptables psmisc ca-certificates python3-virtualenv wget tar

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
## sudo rm -rf /usr/lib/pritunl

sudo mkdir -p /usr/lib/pritunl
sudo mkdir -p /var/lib/pritunl
sudo virtualenv /usr/lib/pritunl

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
### sudo ln -sf /usr/lib/pritunl/bin/pritunl /usr/bin/pritunl

cd ../../
## sudo rm -rf ./pritunl-master

sudo systemctl daemon-reload
sudo systemctl start pritunl
sudo systemctl enable pritunl
