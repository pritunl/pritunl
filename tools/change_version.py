"""Change version."""
import fileinput
import sys

VERSION = sys.argv[1]

for line in fileinput.input('../pritunl/__init__.py', inplace=True):
    if '__version__ = ' in line:
        line = '__version__ = \'%s\'' % VERSION
    print line.rstrip('\n')

for line in fileinput.input('../arch/PKGBUILD', inplace=True):
    if 'pkgver=' in line:
        line = 'pkgver=%s' % VERSION
    print line.rstrip('\n')

for line in fileinput.input('../debian/changelog', inplace=True):
    if 'pritunl (' in line:
        line = 'pritunl (%s-0ubuntu1) unstable; urgency=low' % VERSION
    print line.rstrip('\n')
