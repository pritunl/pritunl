#!/usr/bin/env bash
ntpdate ntp.ubuntu.com
add-apt-repository -y ppa:pritunl/pritunl-testing
apt-get update -qq
apt-get install -qq -y python-flask python-pymongo openvpn devscripts debhelper python-all python-setuptools 1> /dev/null
