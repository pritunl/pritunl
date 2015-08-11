#!/usr/bin/env bash
wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
rpm -i epel-release-7-2.noarch.rpm

yum install -y gcc rpm-build redhat-rpm-config python python-virtualenv python-setuptools python2-devel libffi-devel openssl-devel

mkdir /usr/lib/pritunl
chown vagrant:vagrant /usr/lib/pritunl
