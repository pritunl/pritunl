"""Change version."""
import fileinput
import sys

VERSION = sys.argv[1]

for line in fileinput.input('../pritunl/__init__.py', inplace=True):
    if '__version__ = ' in line:
        line = '__version__ = \'%s\'' % VERSION
    print line.rstrip('\n')

for line in fileinput.input('../PKGBUILD', inplace=True):
    if 'pkgver=' in line:
        line = 'pkgver=%s' % VERSION
    print line.rstrip('\n')
