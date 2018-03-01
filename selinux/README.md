# pritunl-selinux

### setup

```bash
sudo yum -y install policycoreutils-python selinux-policy selinux-policy-devel policycoreutils-newrole policycoreutils-seinfo setools-console
sudo yum -y install pritunl
sudo semodule --disable_dontaudit --build
```

### load module

```bash
cd selinux
ln -s /usr/share/selinux/devel/Makefile
make load
```

### reset file contexts

```bash
sudo restorecon -v -R /tmp/pritunl*
sudo restorecon -v -R /run/pritunl*
sudo restorecon -v /etc/systemd/system/pritunl.service
sudo restorecon -v /usr/lib/systemd/system/pritunl.service
sudo restorecon -v /usr/lib/pritunl/bin/pritunl
sudo restorecon -v /usr/lib/pritunl/bin/python
sudo restorecon -v /usr/lib/pritunl/bin/python2
sudo restorecon -v /usr/lib/pritunl/bin/python2.7
sudo restorecon -v /usr/bin/pritunl-web
sudo restorecon -v /usr/bin/pritunl-dns
sudo restorecon -v -R /var/lib/pritunl
sudo restorecon -v /var/log/pritunl*
```

### clear audit log

```bash
> /var/log/audit/audit.log
```

### run pritunl

```bash
sudo systemctl start pritunl
```

### view logs

```bash
sudo journalctl --follow _SYSTEMD_UNIT=pritunl.service
sudo tail -f /var/log/audit/audit.log | grep pritunl
```

### audit2allow

```bash
audit2allow -a -l
```
