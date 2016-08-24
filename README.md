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

wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
rpm -i epel-release-latest-7.noarch.rpm
yum -y install golang git bzr python2 python-pip net-tools openvpn bridge-utils mongodb-server

echo "export GOPATH=/go" >> ~/.bash_profile
source ~/.bash_profile
go get github.com/pritunl/pritunl-dns
go get github.com/pritunl/pritunl-web
ln -s /go/bin/pritunl-dns /usr/local/bin/pritunl-dns
ln -s /go/bin/pritunl-web /usr/local/bin/pritunl-web

wget https://github.com/pritunl/pritunl/archive/$VERSION.tar.gz
tar xf $VERSION.tar.gz
cd pritunl-$VERSION
python2 setup.py build
pip install -r requirements.txt
python2 setup.py install

systemctl daemon-reload
systemctl start mongod pritunl
systemctl enable mongod pritunl
```

## Stable Repository

### archlinux

```
$ nano /etc/pacman.conf
[pritunl]
Server = http://repo.pritunl.com/stable/pacman

$ pacman-key --keyserver hkp://keyserver.ubuntu.com -r 7568D9BB55FF9E5287D586017AE645C0CF8E292A
$ pacman-key --lsign-key 7568D9BB55FF9E5287D586017AE645C0CF8E292A
$ pacman -Sy
$ pacman -S pritunl mongodb
$ systemctl start mongodb pritunl
$ systemctl enable mongodb pritunl
```

### amazon linux

```
$ sudo nano /etc/yum.repos.d/mongodb-org-3.2.repo
[mongodb-org-3.2]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/amazon/2013.03/mongodb-org/3.2/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-3.2.asc

$ sudo nano /etc/yum.repos.d/pritunl.repo
[pritunl]
name=Pritunl Repository
baseurl=http://repo.pritunl.com/stable/yum/centos/7/
gpgcheck=1
enabled=1

$ gpg --keyserver hkp://keyserver.ubuntu.com --recv-keys 7568D9BB55FF9E5287D586017AE645C0CF8E292A
$ gpg --armor --export 7568D9BB55FF9E5287D586017AE645C0CF8E292A > key.tmp; sudo rpm --import key.tmp; rm -f key.tmp
$ sudo yum install pritunl mongodb-org
$ sudo service mongod start
$ sudo start pritunl
```

### centos 7

```
# SELinux must be disabled

$ sudo nano /etc/yum.repos.d/mongodb-org-3.2.repo
[mongodb-org-3.2]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/3.2/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-3.2.asc

$ nano /etc/yum.repos.d/pritunl.repo
[pritunl]
name=Pritunl Repository
baseurl=http://repo.pritunl.com/stable/yum/centos/7/
gpgcheck=1
enabled=1

$ yum install epel-release
$ gpg --keyserver hkp://keyserver.ubuntu.com --recv-keys 7568D9BB55FF9E5287D586017AE645C0CF8E292A
$ gpg --armor --export 7568D9BB55FF9E5287D586017AE645C0CF8E292A > key.tmp; rpm --import key.tmp; rm -f key.tmp
$ yum install pritunl mongodb-org
$ systemctl start mongod pritunl
$ systemctl enable mongod pritunl
```

### fedora 23

```
# SELinux must be disabled

$ nano /etc/yum.repos.d/pritunl.repo
[pritunl]
name=Pritunl Repository
baseurl=http://repo.pritunl.com/stable/yum/fedora/23/
gpgcheck=1
enabled=1

$ yum install gpg
$ gpg --keyserver hkp://keyserver.ubuntu.com --recv-keys 7568D9BB55FF9E5287D586017AE645C0CF8E292A
$ gpg --armor --export 7568D9BB55FF9E5287D586017AE645C0CF8E292A > key.tmp; rpm --import key.tmp; rm -f key.tmp
$ yum install pritunl mongodb-server
$ systemctl start mongod pritunl
$ systemctl enable mongod pritunl
```

### fedora 24

```
# SELinux must be disabled

$ nano /etc/yum.repos.d/pritunl.repo
[pritunl]
name=Pritunl Repository
baseurl=http://repo.pritunl.com/stable/yum/fedora/24/
gpgcheck=1
enabled=1

$ yum install gpg
$ gpg --keyserver hkp://keyserver.ubuntu.com --recv-keys 7568D9BB55FF9E5287D586017AE645C0CF8E292A
$ gpg --armor --export 7568D9BB55FF9E5287D586017AE645C0CF8E292A > key.tmp; rpm --import key.tmp; rm -f key.tmp
$ yum install pritunl mongodb-server
$ systemctl start mongod pritunl
$ systemctl enable mongod pritunl
```

### debian wheezy

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.2.list
deb http://repo.mongodb.org/apt/debian wheezy/mongodb-org/3.2 main

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/stable/apt wheezy main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 42F3E95A2C4F08279C4960ADD68FA50FEA312927
$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7568D9BB55FF9E5287D586017AE645C0CF8E292A
$ apt-get update
$ apt-get install pritunl mongodb-org
$ service pritunl start
```

### debian jessie

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.2.list
deb http://repo.mongodb.org/apt/debian wheezy/mongodb-org/3.2 main

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/stable/apt jessie main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 42F3E95A2C4F08279C4960ADD68FA50FEA312927
$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7568D9BB55FF9E5287D586017AE645C0CF8E292A
$ apt-get update
$ apt-get install pritunl mongodb-org
$ systemctl start mongod pritunl
$ systemctl enable mongod pritunl
```

### ubuntu precise

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.2.list
deb http://repo.mongodb.org/apt/ubuntu precise/mongodb-org/3.2 multiverse

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/stable/apt precise main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 42F3E95A2C4F08279C4960ADD68FA50FEA312927
$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7568D9BB55FF9E5287D586017AE645C0CF8E292A
$ apt-get update
$ apt-get install pritunl mongodb-org
$ service pritunl start
```

### ubuntu trusty

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.2.list
deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.2 multiverse

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/stable/apt trusty main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 42F3E95A2C4F08279C4960ADD68FA50FEA312927
$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7568D9BB55FF9E5287D586017AE645C0CF8E292A
$ apt-get update
$ apt-get install pritunl mongodb-org
$ service pritunl start
```

### ubuntu xenial

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.2.list
deb http://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.2 multiverse

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/stable/apt xenial main

$ nano /lib/systemd/system/mongod.service
[Unit]
Description=High-performance, schema-free document-oriented database
After=network.target

[Service]
User=mongodb
ExecStart=/usr/bin/mongod --config /etc/mongod.conf

[Install]
WantedBy=multi-user.target

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 42F3E95A2C4F08279C4960ADD68FA50FEA312927
$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7568D9BB55FF9E5287D586017AE645C0CF8E292A
$ apt-get update
$ apt-get install pritunl mongodb-org
$ systemctl start pritunl mongod
$ systemctl enable pritunl mongod
```

### ubuntu yakkety

```
$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/stable/apt yakkety main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7568D9BB55FF9E5287D586017AE645C0CF8E292A
$ apt-get update
$ apt-get install pritunl mongodb-server
$ systemctl start pritunl mongodb
$ systemctl enable pritunl mongodb
```

## License

Please refer to the [`LICENSE`](LICENSE) file for a copy of the license.
