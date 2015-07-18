#!/usr/bin/env bash
ntpdate ntp.ubuntu.com
add-apt-repository -y ppa:pritunl/pritunl-dev
apt-get update -qq
apt-get install -qq -y mongodb-server ntp
sed -i "s/bind_ip = 127.0.0.1/#bind_ip = 127.0.0.1/g" /etc/mongodb.conf
service mongodb restart
