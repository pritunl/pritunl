#!/usr/bin/env bash
wget http://mirrors.rit.edu/fedora/epel/7/x86_64/e/epel-release-7-2.noarch.rpm
rpm -i epel-release-7-2.noarch.rpm

yum install -y gcc rpm-build redhat-rpm-config python python2-devel python-flask pyOpenSSL
