#!/usr/bin/env bash
ntpdate ntp.ubuntu.com
apt-get update -qq
apt-get install -qq -y net-tools openvpn python python-dev python-pip bridge-utils
pip install flask pymongo
