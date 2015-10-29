# pritunl: enterprise vpn server

[![github](https://img.shields.io/badge/github-pritunl-11bdc2.svg?style=flat)](https://github.com/pritunl)
[![twitter](https://img.shields.io/badge/twitter-pritunl-55acee.svg?style=flat)](https://twitter.com/pritunl)

[Pritunl](https://github.com/pritunl/pritunl) is a distributed enterprise
vpn server built using the OpenVPN protocol. Documentation and more
information can be found at the home page [pritunl.com](https://pritunl.com)

[![pritunl](www/img/logo_code.png)](https://pritunl.com)

### Reporting issues

For support or reporting issues please email
[contact@pritunl.com](mailto:contact@pritunl.com)

## Stable Repository

### archlinux

```
$ nano /etc/pacman.conf
[pritunl]
Server = http://repo.pritunl.com/stable/pacman

$ pacman-key --keyserver hkp://keyserver.ubuntu.com -r CF8E292A
$ pacman-key --lsign-key CF8E292A
$ pacman -Sy
$ pacman -S pritunl mongodb
$ systemctl start mongodb pritunl
$ systemctl enable mongodb pritunl
```

### amazon linux

```
$ wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
$ rpm -i epel-release-latest-7.noarch.rpm

$ nano /etc/yum.repos.d/pritunl.repo
[pritunl]
name=Pritunl Repository
baseurl=http://repo.pritunl.com/stable/yum/centos/7/
gpgcheck=1
enabled=1

$ gpg --keyserver hkp://keyserver.ubuntu.com --recv-keys CF8E292A
$ gpg --armor --export CF8E292A > key.tmp; rpm --import key.tmp; rm -f key.tmp
$ yum install pritunl mongodb-server
$ start mongod
$ start pritunl
```

### centos 7

```
$ wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
$ rpm -i epel-release-latest-7.noarch.rpm

$ nano /etc/yum.repos.d/pritunl.repo
[pritunl]
name=Pritunl Repository
baseurl=http://repo.pritunl.com/stable/yum/centos/7/
gpgcheck=1
enabled=1

$ gpg --keyserver hkp://keyserver.ubuntu.com --recv-keys CF8E292A
$ gpg --armor --export CF8E292A > key.tmp; rpm --import key.tmp; rm -f key.tmp
$ yum install pritunl mongodb-server
$ systemctl start mongod pritunl
$ systemctl enable mongod pritunl
```

### fedora 22

```
$ nano /etc/yum.repos.d/pritunl.repo
[pritunl]
name=Pritunl Dev Repository
baseurl=http://repo.pritunl.com/stable/yum/fedora/22/
gpgcheck=1
enabled=1

$ gpg --keyserver hkp://keyserver.ubuntu.com --recv-keys CF8E292A
$ gpg --armor --export CF8E292A > key.tmp; rpm --import key.tmp; rm -f key.tmp
$ yum install pritunl mongodb-server
$ systemctl start mongod pritunl
$ systemctl enable mongod pritunl
```

### debian wheezy

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.0.list
deb http://repo.mongodb.org/apt/debian wheezy/mongodb-org/3.0 main

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/stable/apt wheezy main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7F0CEB10
$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv CF8E292A
$ apt-get update
$ apt-get install pritunl mongodb-org
$ service pritunl start
```

### debian jessie

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.0.list
deb http://repo.mongodb.org/apt/debian wheezy/mongodb-org/3.0 main

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/stable/apt jessie main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7F0CEB10
$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv CF8E292A
$ apt-get update
$ apt-get install pritunl mongodb-org
$ systemctl start mongod pritunl
$ systemctl enable mongod pritunl
```

### ubuntu precise

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.0.list
deb http://repo.mongodb.org/apt/ubuntu precise/mongodb-org/3.0 multiverse

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/stable/apt precise main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7F0CEB10
$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv CF8E292A
$ apt-get update
$ apt-get install pritunl mongodb-org
$ service pritunl start
```

### ubuntu trusty

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.0.list
deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.0 multiverse

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/stable/apt trusty main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7F0CEB10
$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv CF8E292A
$ apt-get update
$ apt-get install pritunl mongodb-org
$ service pritunl start
```

### ubuntu vivid

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.0.list
deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.0 multiverse

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/stable/apt vivid main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7F0CEB10
$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv CF8E292A
$ apt-get update
$ apt-get install pritunl mongodb-org
$ service pritunl start
```

### ubuntu wily

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.0.list
deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.0 multiverse

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/stable/apt wily main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7F0CEB10
$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv CF8E292A
$ apt-get update
$ apt-get install pritunl mongodb-org
$ service pritunl start
```

## Development Repository

**For testing only, not for production use**

### archlinux

```
$ nano /etc/pacman.conf
[pritunl]
Server = http://repo.pritunl.com/dev/pacman

$ pacman-key --keyserver hkp://keyserver.ubuntu.com -r CF8E292A
$ pacman-key --lsign-key CF8E292A
$ pacman -Sy
$ pacman -S pritunl mongodb
$ systemctl start mongodb pritunl
$ systemctl enable mongodb pritunl
```

### amazon linux

```
$ wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
$ rpm -i epel-release-latest-7.noarch.rpm

$ nano /etc/yum.repos.d/pritunl.repo
[pritunl]
name=Pritunl Dev Repository
baseurl=http://repo.pritunl.com/dev/yum/centos/7/
gpgcheck=1
enabled=1

$ gpg --keyserver hkp://keyserver.ubuntu.com --recv-keys CF8E292A
$ gpg --armor --export CF8E292A > key.tmp; rpm --import key.tmp; rm -f key.tmp
$ yum install pritunl mongodb-server
$ start mongod
$ start pritunl
```

### centos 7

```
$ wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
$ rpm -i epel-release-latest-7.noarch.rpm

$ nano /etc/yum.repos.d/pritunl.repo
[pritunl]
name=Pritunl Dev Repository
baseurl=http://repo.pritunl.com/dev/yum/centos/7/
gpgcheck=1
enabled=1

$ gpg --keyserver hkp://keyserver.ubuntu.com --recv-keys CF8E292A
$ gpg --armor --export CF8E292A > key.tmp; rpm --import key.tmp; rm -f key.tmp
$ yum install pritunl mongodb-server
$ systemctl start mongod pritunl
$ systemctl enable mongod pritunl
```

### fedora 22

```
$ nano /etc/yum.repos.d/pritunl.repo
[pritunl]
name=Pritunl Dev Repository
baseurl=http://repo.pritunl.com/dev/yum/fedora/22/
gpgcheck=1
enabled=1

$ gpg --keyserver hkp://keyserver.ubuntu.com --recv-keys CF8E292A
$ gpg --armor --export CF8E292A > key.tmp; rpm --import key.tmp; rm -f key.tmp
$ yum install pritunl mongodb-server
$ systemctl start mongod pritunl
$ systemctl enable mongod pritunl
```

### debian wheezy

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.0.list
deb http://repo.mongodb.org/apt/debian wheezy/mongodb-org/3.0 main

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/dev/apt wheezy main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7F0CEB10
$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv CF8E292A
$ apt-get update
$ apt-get install pritunl mongodb-org
$ service pritunl start
```

### debian jessie

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.0.list
deb http://repo.mongodb.org/apt/debian wheezy/mongodb-org/3.0 main

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/dev/apt jessie main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7F0CEB10
$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv CF8E292A
$ apt-get update
$ apt-get install pritunl mongodb-org
$ systemctl start mongod pritunl
$ systemctl enable mongod pritunl
```

### ubuntu precise

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.0.list
deb http://repo.mongodb.org/apt/ubuntu precise/mongodb-org/3.0 multiverse

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/dev/apt precise main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7F0CEB10
$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv CF8E292A
$ apt-get update
$ apt-get install pritunl mongodb-org
$ service pritunl start
```

### ubuntu trusty

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.0.list
deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.0 multiverse

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/dev/apt trusty main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7F0CEB10
$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv CF8E292A
$ apt-get update
$ apt-get install pritunl mongodb-org
$ service pritunl start
```

### ubuntu vivid

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.0.list
deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.0 multiverse

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/dev/apt vivid main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7F0CEB10
$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv CF8E292A
$ apt-get update
$ apt-get install pritunl mongodb-org
$ service pritunl start
```

### ubuntu wily

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.0.list
deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.0 multiverse

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/dev/apt wily main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7F0CEB10
$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv CF8E292A
$ apt-get update
$ apt-get install pritunl mongodb-org
$ service pritunl start
```

## License

Please refer to the [`LICENSE`](LICENSE) file for a copy of the license.
