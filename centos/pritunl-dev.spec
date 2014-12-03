%define pkgname pritunl
%define pkgver 1.0.0snapshot3
%define pymongo_pkgver 2.7.2

Name: pritunl-dev
Summary: Enterprise VPN Server
Version: %{pkgver}
Release: 1%{?dist}
Group: Applications/Internet
URL: http://%{pkgname}.com/
License: Custom
Source0: https://github.com/%{pkgname}/%{pkgname}/archive/%{pkgver}.tar.gz
Source1: https://github.com/mongodb/mongo-python-driver/archive/%{pymongo_pkgver}.tar.gz
Packager: Pritunl <contact@pritunl.com>

Provides: pritunl = %{version}-%{release}
Provides: python-bson = %{pymongo_pkgver}-%{release}
Provides: python-gridfs = %{pymongo_pkgver}-%{release}
Provides: python-pymongo = %{pymongo_pkgver}-%{release}
Conflicts: pritunl
Conflicts: python-bson
Conflicts: python-gridfs
Conflicts: python-pymongo

Requires: python
Requires: python-flask
Requires: pyOpenSSL
Requires: openvpn
Requires: net-tools

BuildRequires: gcc
BuildRequires: python2-devel
BuildRequires: python-setuptools
BuildRequires: python-flask
BuildRequires: pyOpenSSL

%description
Enterprise vpn server. Documentation and more information can be found at
pritunl.com

%prep
rm -rf $RPM_BUILD_DIR/%{pkgname}-%{pkgver}
rm -rf $RPM_SOURCE_DIR/%{pkgver}.tar.gz
wget https://github.com/%{pkgname}/%{pkgname}/archive/%{pkgver}.tar.gz -P $RPM_SOURCE_DIR/
tar xfz $RPM_SOURCE_DIR/%{pkgver}.tar.gz
wget https://github.com/mongodb/mongo-python-driver/archive/%{pymongo_pkgver}.tar.gz -P $RPM_SOURCE_DIR/
tar xfz $RPM_SOURCE_DIR/%{pymongo_pkgver}.tar.gz

%build
cd $RPM_BUILD_DIR/%{pkgname}-%{pkgver}
python2 setup.py build
cd $RPM_BUILD_DIR/mongo-python-driver-%{pymongo_pkgver}
CFLAGS="%{optflags}" python2 setup.py build

%install
cd $RPM_BUILD_DIR/%{pkgname}-%{pkgver}
mkdir -p $RPM_BUILD_ROOT/var/lib/%{pkgname}
python2 setup.py install --root="$RPM_BUILD_ROOT" --prefix=/usr --no-upstart
cd $RPM_BUILD_DIR/mongo-python-driver-%{pymongo_pkgver}
python2 setup.py install --root="$RPM_BUILD_ROOT" --prefix=/usr

%files
%config /etc/%{pkgname}.conf
/etc/systemd/system/%{pkgname}.service
/usr/bin/%{pkgname}
/usr/lib/python2.7/site-packages/%{pkgname}
/usr/lib/python2.7/site-packages/%{pkgname}-%{pkgver}-*.egg-info
/usr/lib64/python2.7/site-packages/pymongo
/usr/lib64/python2.7/site-packages/pymongo-%{pymongo_pkgver}-*.egg-info
/usr/lib64/python2.7/site-packages/bson
/usr/lib64/python2.7/site-packages/gridfs
/usr/share/%{pkgname}
/var/lib/%{pkgname}
/var/log/%{pkgname}.log
/var/log/%{pkgname}.log.1

%preun
systemctl stop pritunl || true
systemctl disable pritunl || true

%postun
rm -rf /var/lib/%{pkgname}
