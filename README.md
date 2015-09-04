# pritunl: enterprise vpn server

[![archlinux](https://img.shields.io/badge/package-arch%20linux-33aadd.svg?style=flat)](https://pritunl.com/#install)
[![centos](https://img.shields.io/badge/package-centos-669900.svg?style=flat)](https://pritunl.com/#install)
[![github](https://img.shields.io/badge/github-pritunl-11bdc2.svg?style=flat)](https://github.com/pritunl)
[![twitter](https://img.shields.io/badge/twitter-pritunl-55acee.svg?style=flat)](https://twitter.com/pritunl)

[Pritunl](https://github.com/pritunl/pritunl) is a distributed enterprise
vpn server built using the OpenVPN protocol. Documentation and more
information can be found at the home page [pritunl.com](https://pritunl.com)

[![pritunl](www/img/logo_code.png)](https://pritunl.com)

## Development Builds

For testing only

### archlinux

```
$ nano /etc/pacman.conf
[pritunl]
Server = http://repo.pritunl.com/dev/pacman

$ pacman-key --keyserver hkp://pgp.mit.edu -r CF8E292A
$ pacman-key --lsign-key CF8E292A
$ pacman -Sy
$ pacman -S pritunl
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

$ gpg --keyserver hkp://pgp.mit.edu --recv-keys CF8E292A
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

$ gpg --keyserver hkp://pgp.mit.edu --recv-keys CF8E292A
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
$ apt-key adv --keyserver hkp://pgp.mit.edu --recv CF8E292A
$ apt-get update
$ apt-get install pritunl
$ systemctl start mongod pritunl
$ systemctl enable mongod pritunl
```

### debian jessie

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.0.list
deb http://repo.mongodb.org/apt/debian wheezy/mongodb-org/3.0 main

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/dev/apt jessie main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7F0CEB10
$ apt-key adv --keyserver hkp://pgp.mit.edu --recv CF8E292A
$ apt-get update
$ apt-get install pritunl
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
$ apt-key adv --keyserver hkp://pgp.mit.edu --recv CF8E292A
$ apt-get update
$ apt-get install pritunl
$ service pritunl start
```

### ubuntu trusty

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.0.list
deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.0 multiverse

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/dev/apt trusty main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7F0CEB10
$ apt-key adv --keyserver hkp://pgp.mit.edu --recv CF8E292A
$ apt-get update
$ apt-get install pritunl
$ service pritunl start
```

### ubuntu vivid

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.0.list
deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.0 multiverse

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/dev/apt vivid main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7F0CEB10
$ apt-key adv --keyserver hkp://pgp.mit.edu --recv CF8E292A
$ apt-get update
$ apt-get install pritunl
$ service pritunl start
```

### ubuntu wily

```
$ nano /etc/apt/sources.list.d/mongodb-org-3.0.list
deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.0 multiverse

$ nano /etc/apt/sources.list.d/pritunl.list
deb http://repo.pritunl.com/dev/apt wily main

$ apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7F0CEB10
$ apt-key adv --keyserver hkp://pgp.mit.edu --recv CF8E292A
$ apt-get update
$ apt-get install pritunl
$ service pritunl start
```

## License

Please refer to the [`LICENSE`](LICENSE) file for a copy of the license.

## Export Requirements

You may not export or re-export this software or any copy or adaptation in
violation of any applicable laws or regulations.

Without limiting the generality of the foregoing, hardware, software,
technology or services provided under this license agreement may not be
exported, reexported, transferred or downloaded to or within (or to a national
resident of) countries under U.S. economic embargo including the following
countries:

Cuba, Iran, Libya, North Korea, Sudan and Syria. This list is subject to
change.

Hardware, software, technology or services may not be exported, reexported,
transferred or downloaded to persons or entities listed on the U.S. Department
of Commerce Denied Persons List, Entity List of proliferation concern or on
any U.S. Treasury Department Designated Nationals exclusion list, or to
parties directly or indirectly involved in the development or production of
nuclear, chemical, biological weapons or in missile technology programs as
specified in the U.S. Export Administration Regulations (15 CFR 744).

By accepting this license agreement you confirm that you are not located in
(or a national resident of) any country under U.S. economic embargo, not
identified on any U.S. Department of Commerce Denied Persons List, Entity List
or Treasury Department Designated Nationals exclusion list, and not directly
or indirectly involved in the development or production of nuclear, chemical,
biological weapons or in missile technology programs as specified in the U.S.
Export Administration Regulations.

Software available on this web site contains cryptography and is therefore
subject to US government export control under the U.S. Export Administration
Regulations ("EAR"). EAR Part 740.13(e) allows the export and reexport of
publicly available encryption source code that is not subject to payment of
license fee or royalty payment. Object code resulting from the compiling of
such source code may also be exported and reexported under this provision if
publicly available and not subject to a fee or payment other than reasonable
and customary fees for reproduction and distribution. This kind of encryption
source code and the corresponding object code may be exported or reexported
without prior U.S. government export license authorization provided that the
U.S. government is notified about the Internet location of the software.

The software available on this web site is publicly available without license
fee or royalty payment, and all binary software is compiled from the source
code. The U.S. government has been notified about this site and the location
site for the source code. Therefore, the source code and compiled object code
may be downloaded and exported under U.S. export license exception (without a
U.S. export license) in accordance with the further restrictions outlined
above regarding embargoed countries, restricted persons and restricted end
uses.

Local Country Import Requirements. The software you are about to download
contains cryptography technology. Some countries regulate the import, use
and/or export of certain products with cryptography. Pritunl makes no
claims as to the applicability of local country import, use and/or export
regulations in relation to the download of this product. If you are located
outside the U.S. and Canada you are advised to consult your local country
regulations to insure compliance.
