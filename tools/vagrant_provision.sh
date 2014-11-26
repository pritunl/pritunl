#!/usr/bin/env bash
ntpdate ntp.ubuntu.com

add-apt-repository -y ppa:pritunl/pritunl-testing

apt-get update -qq

# Dev requirements
apt-get install -qq -y python-flask python-cherrypy3 python-objgraph python-pymongo openvpn htop

# Build requirements
apt-get install -qq -y devscripts debhelper python-all python-setuptools 1> /dev/null

# Rng-tools
apt-get install -qq -y rng-tools
echo "HRNGDEVICE=/dev/urandom" | tee /etc/default/rng-tools
/etc/init.d/rng-tools start
