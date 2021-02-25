# pritunl: enterprise vpn server

[![github](https://img.shields.io/badge/github-pritunl-11bdc2.svg?style=flat)](https://github.com/pritunl)
[![twitter](https://img.shields.io/badge/twitter-pritunl-55acee.svg?style=flat)](https://twitter.com/pritunl)

[Pritunl](https://github.com/pritunl/pritunl) is a distributed enterprise
vpn server built using the OpenVPN protocol. Documentation and more
information can be found at the home page [pritunl.com](https://pritunl.com)

[![pritunl](www/img/logo_code.png)](https://pritunl.com)

## Install From Source

```bash
export VERSION=X.XX.XX.XX # Set current pritunl version here

sudo yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
sudo yum -y install python3-pip python3-devel gcc git openvpn openssl net-tools iptables psmisc ca-certificates

wget https://golang.org/dl/go1.15.7.linux-amd64.tar.gz
echo "0d142143794721bb63ce6c8a6180c4062bcf8ef4715e7d6d6609f3a8282629b3 go1.15.7.linux-amd64.tar.gz" | sha256sum -c -

sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xf go1.15.7.linux-amd64.tar.gz
rm -f go1.15.7.linux-amd64.tar.gz
tee -a ~/.bashrc << EOF
export GOPATH=\$HOME/go
export PATH=/usr/local/go/bin:\$PATH
EOF
source ~/.bashrc

go get -u github.com/pritunl/pritunl-dns
go get -u github.com/pritunl/pritunl-web
sudo ln -sf ~/go/bin/pritunl-dns /usr/bin/pritunl-dns
sudo ln -sf ~/go/bin/pritunl-web /usr/bin/pritunl-web

wget https://github.com/pritunl/pritunl/archive/$VERSION.tar.gz
tar xf $VERSION.tar.gz
cd pritunl-master
python3 setup.py build
sudo pip3 install -U -r requirements.txt
sudo python3 setup.py install
sudo ln -sf /usr/local/bin/pritunl /usr/bin/pritunl

sudo systemctl daemon-reload
sudo systemctl start mongod pritunl
sudo systemctl enable mongod pritunl
```

## License

Please refer to the [`LICENSE`](LICENSE) file for a copy of the license.
