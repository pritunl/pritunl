# pritunl-selinux

### setup

```bash
yum -y install policycoreutils-newrole policycoreutils-seinfo setools-console
yum -y install pritunl
semodule --disable_dontaudit --build
```

### load module

```bash
cd selinux
ln -s /usr/share/selinux/devel/Makefile
make load
```

### load web module

```bash
cd selinux-web
ln -s /usr/share/selinux/devel/Makefile
make load
```

### reset file contexts

```bash
rm -rf /var/lib/pritunl
rm -rf /tmp/pritunl*
rm -rf /run/pritunl.
restorecon -v /etc/systemd/system/pritunl.service
restorecon -v /usr/lib/systemd/system/pritunl.service
restorecon -v /usr/lib/pritunl/bin/pritunl
restorecon -v /usr/lib/pritunl/bin/python
restorecon -v /usr/lib/pritunl/bin/python2
restorecon -v /usr/lib/pritunl/bin/python2.7
```

### run pritunl

```bash
systemctl start pritunl
```

### view logs

```bash
journalctl --follow _SYSTEMD_UNIT=pritunl.service
tail -f /var/log/audit/audit.log | grep type=AVC
```

### audit2allow

```bash
audit2allow -a -l
```
