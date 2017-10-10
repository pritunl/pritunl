#!/bin/bash
echo -e "[pritunl]\nname=Pritunl Repository\nbaseurl=http://repo.pritunl.com/stable/yum/centos/7/\ngpgcheck=1\nenabled=1" > /etc/yum.repos.d/pritunl.repo
echo -e "description \"Pritunl Override\"\n\nstart on starting pritunl\nstop on runlevel [!2345]\n\npre-start script\n  stop pritunl\n  sleep 1\nend script" > /etc/init/pritunl-override.conf
echo -e "\nyum -y clean all\nyum -y upgrade\nsleep 1\nstart pritunl" >> /etc/rc.local
gpg --keyserver hkp://keyserver.ubuntu.com --recv-keys 7568D9BB55FF9E5287D586017AE645C0CF8E292A
gpg --armor --export 7568D9BB55FF9E5287D586017AE645C0CF8E292A > key.tmp
rpm --import key.tmp
rm -f key.tmp
yum -y upgrade
yum -y install pritunl
