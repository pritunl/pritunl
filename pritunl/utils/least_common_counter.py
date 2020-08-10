import collections
import heapq
import operator

class LeastCommonCounter(collections.Counter):
    def least_common(self, n=None):
        if n is None:
            return sorted(iter(list(self.items())), key=operator.itemgetter(1))
        return heapq.nsmallest(n, iter(list(self.items())), key=operator.itemgetter(1))
