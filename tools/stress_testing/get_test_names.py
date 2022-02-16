# pylama:ignore=
COUNT = 60000

for i in xrange(1, COUNT + 1):  # FIXME E0602 undefined name 'xrange' [pyflakes]
    print('user_%s' % str(i).zfill(5))
