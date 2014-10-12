#!/usr/bin/env bash
ntpdate ntp.ubuntu.com

apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
echo "deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen" | tee /etc/apt/sources.list.d/mongodb.list

apt-get update -qq

apt-get install -qq -y mongodb-org ntp

sed -i "s/bind_ip = 127.0.0.1/#bind_ip = 127.0.0.1/g" /etc/mongod.conf
service mongod restart
