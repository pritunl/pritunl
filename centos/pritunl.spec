%define pkgname pritunl
%define pkgver 1.3.662.15
%define pkgrelease 1

Name: %{pkgname}
Summary: Enterprise VPN Server
Version: %{pkgver}
Release: %{pkgrelease}%{?dist}
Group: Applications/Internet
URL: http://%{pkgname}.com/
License: Custom
Source0: https://github.com/%{pkgname}/%{pkgname}/archive/%{pkgver}.tar.gz
Packager: Pritunl <contact@pritunl.com>

Provides: pritunl = %{version}-%{release}
Conflicts: pritunl
Conflicts: pritunl-dev

Requires: python2
Requires: openvpn
Requires: net-tools

BuildRequires: gcc
BuildRequires: python2-devel
BuildRequires: python-setuptools
BuildRequires: python-virtualenv

%description
Enterprise vpn server. Documentation and more information can be found at
pritunl.com

%prep
rm -rf /usr/lib/%{pkgname}/*
rm -rf $RPM_BUILD_DIR/%{pkgname}-%{pkgver}
rm -rf $RPM_SOURCE_DIR/%{pkgver}.tar.gz
wget https://github.com/%{pkgname}/%{pkgname}/archive/%{pkgver}.tar.gz -P $RPM_SOURCE_DIR/
tar xfz $RPM_SOURCE_DIR/%{pkgver}.tar.gz

%build
cd $RPM_BUILD_DIR/%{pkgname}-%{pkgver}
python2 setup.py build
virtualenv /usr/lib/%{pkgname}
/usr/lib/%{pkgname}/bin/pip install -r requirements.txt

%install
cd $RPM_BUILD_DIR/%{pkgname}-%{pkgver}
mkdir -p $RPM_BUILD_ROOT/var/lib/%{pkgname}
/usr/lib/%{pkgname}/bin/python2 setup.py install --root="$RPM_BUILD_ROOT" --prefix=/usr
rm -r $RPM_BUILD_ROOT/etc/init.d/%{pkgname}.sh
cp -r $RPM_BUILD_ROOT/usr/lib/python2.7/site-packages /usr/lib/%{pkgname}/lib/python2.7
rm -r $RPM_BUILD_ROOT/usr/lib/python2.7
mkdir -p $RPM_BUILD_ROOT/usr/lib/%{pkgname}
cp -r /usr/lib/%{pkgname}/* $RPM_BUILD_ROOT/usr/lib/%{pkgname}/

%files
%config /etc/%{pkgname}.conf
/etc/init/%{pkgname}.conf
/etc/systemd/system/%{pkgname}.service
/usr/bin/%{pkgname}
/usr/lib/%{pkgname}
/usr/share/%{pkgname}
/var/lib/%{pkgname}
/var/log/%{pkgname}.log
/var/log/%{pkgname}.log.1

%preun
systemctl stop pritunl || true
systemctl disable pritunl || true
