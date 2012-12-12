import itertools
import collections
import operator

class Relation(object):
    def __init__(self, seq):
        self._iter = seq

    def param(self, name):
        ''' extracts param "name" from a dict

        >>> x = Relation([{'a': 1}, {'a': 2}])
        >>> list(x.param('a'))
        [1, 2]
        '''
        return itertools.imap(lambda o: o.get(name), self._iter)

    def params(self, *names):
        ''' returns tuples of projected names

        >>> x = Relation([{'a': 1, 'b': 2}]).params('a', 'b')
        >>> list(x)
        [(1, 2)]
        '''
        return itertools.imap(operator.itemgetter(*names), self._iter)

    def compute(self, paramDict):
        ''' computes additional parameters to the object, according paramDict

        >>> x = Relation([{'a': 1}]).compute({'c': lambda o: o['a'] + 1})
        >>> list(x)
        [{'a': 1, 'c': 2}]
        '''
        def setter(o):
            o.update(dict((name, func(o)) for name, func in paramDict.items()))
            return o
        return self.map(setter)

    def project(self, *names):
        ''' return subset of attributes

        >>> x = Relation([{'a': 1, 'b': 2, 'c': 3}]).project('a', 'b')
        >>> list(x)
        [{'a': 1, 'b': 2}]
        '''
        return self.map(lambda o: dict((k, o.get(k)) for k in names))

    def map(self, func):
        return self.__class__(itertools.imap(func, self._iter))

    def filter(self, func):
        ''' return only attributes accepted by function func

        >>> x = Relation([{'a': 1}, {'a': 2}, {'a': 3}]).filter(lambda o: o['a'] < 3)
        >>> list(x.param('a'))
        [1, 2]
        '''
        return self.__class__(itertools.ifilter(func, self._iter))

    def __iter__(self):
        for x in self._iter:
            yield x

    def rename(self, **kwargs):
        ''' rename some attributes according kwargs mapping

        >>> x = Relation([{'a': 1, 'b': 2}]).rename(a='c')
        >>> list(x)
        [{'c': 1, 'b': 2}]
        '''
        func = lambda o: dict((kwargs.get(k, k), o[k]) for k in o)
        return self.map(func)

    def fix(self):
        ''' materialize data so it is possible to iterate it twice

        >>> it = iter([{'a': 1, 'b': 2}])
        >>> rel = Relation(it).fix()
        >>> list(rel)
        [{'a': 1, 'b': 2}]
        >>> list(rel)
        [{'a': 1, 'b': 2}]
        '''
        return self.__class__(list(self._iter))

    def copy(self):
        return self.map(dict)

    def count(self):
        ''' returns number of elements

        >>> Relation([{'a': 1}, {'a': 2}]).count()
        2
        '''
        return len(self._iter)

    def sortBy(self, keyFunc):
        ''' sorts items

        >>> x = Relation([{'a': 3}, {'a': 1}, {'a': 2}]).sortBy(lambda o: o['a'])
        >>> list(x.param('a'))
        [1, 2, 3]
        '''
        array = list(self._iter)
        array.sort(key=keyFunc)
        return self.__class__(array)

    def sortByNames(self, *names):
        ''' sorts items

        >>> x = Relation([{'a': 3}, {'a': 1}, {'a': 2}]).sortByNames('a')
        >>> list(x.param('a'))
        [1, 2, 3]
        '''
        return self.sortBy(keyFunc=operator.itemgetter(*names))

    @staticmethod
    def _checkNonDecreasing(it, keyFunc):
        prev = it.next()
        yield prev
        prevValue = keyFunc(prev)
        while True:
            current = it.next()
            currentValue = keyFunc(current)
            if currentValue < prevValue:
                raise RuntimeError('the relation is not sorted')
            yield current
            prevValue = currentValue

    def groupBy(self, keyFunc, isSorted=False):
        ''' sorts and groups items return iterables
        '''
        if isSorted:
            it = self._checkNonDecreasing(self._iter, keyFunc)
        else:
            it = list(self._iter)
            it.sort(key=keyFunc)
        return self.__class__((k, self.__class__(g)) for k, g in itertools.groupby(it, keyFunc))

    def groupByNames(self, isSorted=False, *names):
        ''' sorts and groups items
        '''
        return self.groupBy(keyFunc=operator.itemgetter(*names), isSorted=isSorted)

    def mapping(self, keyFunc):
        ''' returns mapping of key to value
        '''
        mapping = {}
        for v in self._iter:
            k = keyFunc(v)
            if k in mapping:
                raise RuntimeError('mapping key is not unique')
            mapping[k] = v

    def mappingByNames(self, *names):
        return self.mapping(keyFunc=operator.itemgetter(*names))

    def takeWhile(self, func):
        ''' take arguments while func holds and forget the rest
        '''
        return self.__class__(itertools.takewhile(func, self._iter))

    def dropWhile(self, func):
        ''' skip arguments until func holds and returns the rest
        '''
        return self.__class__(itertools.dropwhile(func, self._iter))

    def skip(self, n):
        ''' skip first n arguments and returns the rest
        '''
        return self.__class__(itertools.islice(self._iter, n, None))

    def take(self, n):
        ''' takes first n arguments (or less if there are less items)
        '''
        return self.__class__(itertools.islice(self._iter, 0, n))

    def reduce(self, func):
        ''' reduces all elements to one element

        usefull e.g. for implementing max, min, sum
        @param func takes two arguments and returns one
        '''
        return reduce(func, self._iter)

    def max(self, keyFunc):
        return max(self._iter, key=keyFunc)

    def min(self, keyFunc):
        return min(self._iter, key=keyFunc)

    def countBy(self, keyFunc):
        ''' compute and sort items according function
        '''
        return collections.Counter(keyFunc(v) for v in self._iter)

    def countByNames(self, *names):
        ''' compute count of unique combinations
        '''
        return self.countBy(keyFunc=operator.itemgetter(*names))

identity = lambda x: x
