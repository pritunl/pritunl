import collections
import heapq
import operator

class LeastCommonCounter(collections.Counter):
    def least_common(self, n=None):
        if n is None:
            return sorted(self.iteritems(), key=operator.itemgetter(1))
        return heapq.nsmallest(n, self.iteritems(), key=operator.itemgetter(1))
