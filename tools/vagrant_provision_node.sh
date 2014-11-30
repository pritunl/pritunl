#!/usr/bin/env bash
ntpdate ntp.ubuntu.com
add-apt-repository -y ppa:pritunl/pritunl-dev
apt-get update -qq
apt-get install -qq -y python-flask python-cherrypy3 python-objgraph python-pymongo openvpn htop rng-tools
echo "HRNGDEVICE=/dev/urandom" | tee /etc/default/rng-tools
/etc/init.d/rng-tools start
