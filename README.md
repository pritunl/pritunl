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
[mongodb-org]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/9/mongodb-org/8.2/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-8.0.asc
EOF

sudo dnf -y install mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod

# Install OpenVPN
sudo tee /etc/yum.repos.d/pritunl.repo << EOF
[pritunl]
name=Pritunl Repository
baseurl=https://repo.pritunl.com/stable/yum/oraclelinux/9/
gpgcheck=1
enabled=1
gpgkey=https://raw.githubusercontent.com/pritunl/pgp/master/pritunl_repo_pub.asc
EOF

sudo dnf --allowerasing -y install pritunl-openvpn

# [Optional] Install ndppd for IPv6 NDP proxying
sudo dnf -y install pritunl-ndppd

# Set current pritunl version X.XX.XXXX.XX
export VERSION="X.XX.XXXX.XX"

sudo dnf -y install gcc git-core wget rsync openssl-devel bzip2-devel libffi-devel sqlite-devel xz-devel zlib-devel selinux-policy selinux-policy-devel policycoreutils-python-utils python3 net-tools openssl iptables ipset ca-certificates psmisc

wget https://www.python.org/ftp/python/3.9.23/Python-3.9.23.tar.xz
echo "61a42919e13d539f7673cf11d1c404380e28e540510860b9d242196e165709c9 Python-3.9.23.tar.xz" | sha256sum -c - && tar xf Python-3.9.23.tar.xz
rm Python-3.9.23.tar.xz

cd "./Python-3.9.23"
gcc_major=$(gcc -dumpversion | cut -d. -f1)
base_cflags="-fstack-protector-strong -Wp,-D_FORTIFY_SOURCE=2 -Wp,-D_GLIBCXX_ASSERTIONS -Werror=format-security -mtune=generic -grecord-gcc-switches"
if [ "$gcc_major" -ge 7 ]; then
    gcc7_flags="-fno-semantic-interposition"
    cflags="$base_cflags $gcc7_flags"
    ldflags="-fno-semantic-interposition"
else
    cflags="$base_cflags"
    ldflags=""
fi
if [ "$gcc_major" -ge 8 ]; then
    gcc8_flags="-fstack-clash-protection -fcf-protection"
    cflags="$cflags $gcc8_flags"
fi
if [ "$gcc_major" -ge 11 ]; then
    arch_flags="-march=x86-64-v2"
    cflags="$cflags $arch_flags"
fi
export CFLAGS_NODIST="$cflags"
export LDFLAGS_NODIST="$ldflags"
sudo rm -rf /usr/lib/pritunl
sudo mkdir /usr/lib/pritunl
./configure --prefix=/usr --libdir=/usr/lib --enable-optimizations --enable-ipv6 --enable-loadable-sqlite-extensions --disable-shared --with-lto --with-computed-gotos=yes --with-platlibdir=lib
sudo make DESTDIR="/usr/lib/pritunl" install
cd ../
sudo rm -rf ./Python-3.9.23
sudo /usr/lib/pritunl/usr/bin/python3 -m ensurepip
sudo /usr/lib/pritunl/usr/bin/python3 -m pip install pip==23.3.2

sudo rm -rf /usr/local/go
wget https://go.dev/dl/go1.25.5.linux-amd64.tar.gz
echo "9e9b755d63b36acf30c12a9a3fc379243714c1c6d3dd72861da637f336ebb35b go1.25.5.linux-amd64.tar.gz" | sha256sum -c - && sudo tar -C /usr/local -xf go1.25.5.linux-amd64.tar.gz
rm -f go1.25.5.linux-amd64.tar.gz

tee -a ~/.bashrc << 'EOF'
export GOPATH=$HOME/go
export GOROOT=/usr/local/go
export PATH=/usr/local/go/bin:$PATH
EOF
source ~/.bashrc

sudo systemctl stop pritunl || true

sudo mkdir -p /var/lib/pritunl

go install -v github.com/pritunl/pritunl-web@latest
go install -v github.com/pritunl/pritunl-dns@latest
sudo rm -f /usr/bin/pritunl-dns
sudo rm -f /usr/bin/pritunl-web
sudo cp -f ~/go/bin/pritunl-dns /usr/bin/pritunl-dns
sudo cp -f ~/go/bin/pritunl-web /usr/bin/pritunl-web

wget https://github.com/pritunl/pritunl/archive/refs/tags/$VERSION.tar.gz
tar xf $VERSION.tar.gz
rm $VERSION.tar.gz
cd ./pritunl-$VERSION
sudo /usr/lib/pritunl/usr/bin/pip3 install --require-hashes -r requirements.txt
/usr/lib/pritunl/usr/bin/python3 setup.py build
sudo /usr/lib/pritunl/usr/bin/python3 setup.py install
sudo ln -sf /usr/lib/pritunl/usr/bin/pritunl /usr/bin/pritunl

sudo groupadd -r pritunl-web || true
sudo useradd -r -g pritunl-web -s /sbin/nologin -c 'Pritunl web server' pritunl-web || true

# [Optional] SELinux profile
cd selinux9
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

cd ../../
sudo rm -rf ./pritunl-$VERSION

sudo systemctl daemon-reload
sudo systemctl start pritunl
sudo systemctl enable pritunl
```

## License

Please refer to the [`LICENSE`](LICENSE) file for a copy of the license.
