#!/usr/bin/env bash
apt-get install -qq -y python-software-properties 1> /dev/null

add-apt-repository -y ppa:pritunl/pritunl-testing 1> /dev/null

apt-get update -qq 1> /dev/null

# Dev requirements
apt-get install -qq -y python-pip python-flask python-cherrypy3 python-crypto python-objgraph python-pymongo openvpn htop 1> /dev/null

# Build requirements
apt-get install -qq -y devscripts debhelper python-all python-setuptools 1> /dev/null

# Rng-tools
apt-get install -qq -y rng-tools 1> /dev/null
echo "HRNGDEVICE=/dev/urandom" > /etc/default/rng-tools
/etc/init.d/rng-tools start
