%define pkgname pritunl
%define pkgver 0.10.12

Name: %{pkgname}
Summary: Pritunl vpn server
Version: %{pkgver}
Release: 1%{?dist}
Group: Applications/Internet
URL: http://%{pkgname}.com/
License: Custom
Source0: https://github.com/%{pkgname}/%{pkgname}/archive/%{pkgver}.tar.gz
Packager: Zachary Huff <zach.huff.386@gmail.com>
Provides: pritunl
Requires: python
Requires: python-flask
Requires: python-cherrypy
Requires: python-crypto
Requires: openvpn
Requires: net-tools

%description
Open source vpn server. Documentation and more information can be found at
the home page pritunl.com

%prep
rm -rf $RPM_BUILD_DIR/%{pkgname}-%{pkgver}
rm -rf $RPM_SOURCE_DIR/%{pkgver}.tar.gz
wget https://github.com/%{pkgname}/%{pkgname}/archive/%{pkgver}.tar.gz -P $RPM_SOURCE_DIR/
tar -xf $RPM_SOURCE_DIR/%{pkgver}.tar.gz

%build
cd $RPM_BUILD_DIR/%{pkgname}-%{pkgver}
python2 setup.py build

%install
cd $RPM_BUILD_DIR/%{pkgname}-%{pkgver}
mkdir -p $RPM_BUILD_ROOT/var/lib/%{pkgname}
python2 setup.py install --root="$RPM_BUILD_ROOT" --prefix=/usr --no-upstart

%files
%config /etc/%{pkgname}.conf
/etc/systemd/system/%{pkgname}.service
/usr/bin/%{pkgname}
/usr/lib/python2.7/site-packages/%{pkgname}
/usr/lib/python2.7/site-packages/%{pkgname}-%{pkgver}-py2.7.egg-info
/usr/share/%{pkgname}
/var/lib/%{pkgname}
/var/log/%{pkgname}.log
/var/log/%{pkgname}.log.1

%preun
systemctl stop pritunl || true
systemctl disable pritunl || true

%postun
rm -rf /var/lib/%{pkgname}
