# pylama:ignore=E0100
COUNT = 60000

for i in xrange(1, COUNT + 1):
    print 'user_%s' % str(i).zfill(5)  # FIXME SyntaxError, pylama ignore won't hide
