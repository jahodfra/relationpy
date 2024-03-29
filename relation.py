import sys
import itertools
import collections
import operator
import inspect

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

    def extend(self, **newParams):
        ''' computes additional parameters to the object

        >>> Relation([{'a': 1, 'b': 2}]).extend(
        ...     c=lambda a: a + 1,
        ...     d=lambda a, b: a + b,
        ...     e=lambda: 25).list()
        [{'a': 1, 'c': 2, 'b': 2, 'e': 25, 'd': 3}]
        '''
        def createComputeParam(func):
            args = inspect.getargspec(func).args
            if len(args) == 0:
                return lambda o: func()
            elif len(args) == 1:
                arg = args[0]
                return lambda o: func(o.get(arg))
            else:
                getArgs = operator.itemgetter(*args)
                return lambda o: func(*getArgs(o))

        computeParam = dict((name, createComputeParam(func)) for name, func in newParams.items())
        def setter(o):
            newValues = dict((name, func(o)) for name, func in computeParam.items())
            o.update(newValues)
            return o
        return self.map(setter)

    def project(self, *names):
        ''' return subset of attributes

        >>> Relation([{'a': 1, 'b': 2, 'c': 3}]).project('a', 'b').list()
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

        >>> Relation([{'a': 1, 'b': 2}]).rename(c='a').list()
        [{'c': 1, 'b': 2}]
        '''
        revertedDict = dict((v, k) for k, v in kwargs.items())
        func = lambda o: dict((revertedDict.get(k, k), v) for k, v in o.items())
        return self.map(func)

    def fix(self):
        ''' materialize data so it is possible to iterate it twice

        >>> it = iter([{'a': 1, 'b': 2}])
        >>> rel = Relation(it).fix()
        >>> rel.list()
        [{'a': 1, 'b': 2}]
        >>> rel.list()
        [{'a': 1, 'b': 2}]
        '''
        return self.__class__(list(self._iter))

    def list(self):
        return list(self._iter)

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
        ascending = False
        descending = False

        it = iter(it)
        prev = it.next()
        yield prev
        prevValue = keyFunc(prev)
        while True:
            current = it.next()
            currentValue = keyFunc(current)
            if prevValue > currentValue:
                if ascending:
                    raise RuntimeError('the relation is not sorted')
                descending = True
            elif prevValue < currentValue:
                if descending:
                    raise RuntimeError('the relation is not sorted')
                ascending = True
            yield current
            prevValue = currentValue

    def _groupBy(self, keyFunc, isSorted=False):
        ''' sorts and groups items return iterables
        '''
        if isSorted:
            it = self._checkNonDecreasing(self._iter, keyFunc)
        else:
            it = list(self._iter)
            it.sort(key=keyFunc)
        return itertools.groupby(it, keyFunc)

    def groupBy(self, keyFunc, isSorted=False):
        buildDict = lambda (key, group): {'key': key, 'group': group}
        return self.__class__(itertools.imap(buildDict, self._groupBy(keyFunc, isSorted)))

    def groupByNames(self, *names, **kwargs):
        ''' sorts and groups items

        Check that unsorted relation will throw an error
        >>> Relation([{'a': 2}, {'a': 1}, {'a': 2}]).groupByNames('a',
        ...     isSorted=True).list()
        Traceback (most recent call last):
        RuntimeError: the relation is not sorted

        Check that sorted relation, can be returned without any problem (ascending)
        >>> Relation([{'a': 1}, {'a': 1}, {'a': 2}]).groupByNames('a',
        ...     isSorted=True).list()
        [{'a': 1, 'group': [{'a': 1}, {'a': 1}]}, {'a': 2, 'group': [{'a': 2}]}]

        Check that sorted relation, can be returned without any problem (descending)
        >>> Relation([{'a': 2}, {'a': 1}, {'a': 1}]).groupByNames('a',
        ...     isSorted=True).list()
        [{'a': 2, 'group': [{'a': 2}]}, {'a': 1, 'group': [{'a': 1}, {'a': 1}]}]

        Check the grouping with sorting
        >>> Relation([{'a': 2}, {'a': 1}, {'a': 2}]).groupByNames('a').list()
        [{'a': 1, 'group': [{'a': 1}]}, {'a': 2, 'group': [{'a': 2}, {'a': 2}]}]
        '''
        keyFunc = operator.itemgetter(*names)
        isSorted = kwargs.get('isSorted', False)
        def buildDict((key, group)):
            d = {'group': list(group)}
            if len(names) == 1:
                d[names[0]] = key
            else:
                for k, v in zip(names, key):
                    d[k] = v
            return d
        return self.__class__(itertools.imap(buildDict, self._groupBy(keyFunc, isSorted)))

    def mapping(self, keyFunc):
        ''' returns mapping of key to value

        Test mapping according a custom key
        >>> f = lambda o: o['a'] * 3
        >>> Relation([{'a': 1}, {'a': 2}, {'a': 3}]).mapping(f)
        {9: {'a': 3}, 3: {'a': 1}, 6: {'a': 2}}

        Test duplicit key
        >>> Relation([{'a': 1}, {'a': 2}, {'a': 2}]).mapping(f)
        Traceback (most recent call last):
        RuntimeError: mapping key is not unique
        '''
        mapping = {}
        for v in self._iter:
            k = keyFunc(v)
            if k in mapping:
                raise RuntimeError('mapping key is not unique')
            mapping[k] = v
        return mapping

    def mappingByNames(self, *names):
        ''' mapping version with key equal to names
        >>> Relation([{'a': 1}, {'a': 2}, {'a': 3}]).mappingByNames('a')
        {1: {'a': 1}, 2: {'a': 2}, 3: {'a': 3}}
        '''
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

    def printTable(self, keys=None, maxWidth=120, separator='    '):
        '''function to printout results in table like format
        '''
        items = list(self._iter)

        if isinstance(keys, basestring):
            keys = keys.split()
        elif not keys:
            keys = set()
            for obj in items:
                keys.update(obj.keys())
            keys = list(keys)
            keys.sort()
        rows = []
        for obj in items:
            rows.append(tuple(obj.get(k) for k in keys))
        TablePrinter(maxWidth=maxWidth, separator=separator).write(keys, rows)


class TablePrinter:
    def __init__(self, maxWidth, separator):
        self.maxWidth = maxWidth
        self.separator = separator

    def write(self, keys, rows, fout=None):
        if not fout:
            fout = sys.stdout
        fieldSizes = map(len, keys)
        formattedRows = []
        for row in rows:
            formattedRow = [unicode(field) if field is not None else '' for field in row]
            formattedRows.append(formattedRow)
            for i, field in enumerate(formattedRow):
                fieldSizes[i] = max(fieldSizes[i], len(field))

        separatorSize = len(self.separator)
        longestRow = sum(fieldSizes) + (len(keys) - 1) * separatorSize
        if longestRow <= self.maxWidth:
            fout.write(self.separator.join(k.ljust(fieldSizes[i]) for i, k in enumerate(keys)))
            fout.write('\n')
            fout.write('-' * longestRow)
            fout.write('\n')
            for row in formattedRows:
                fout.write(self.separator.join(field.rjust(fieldSizes[i]) for i, field in enumerate(row)))
                fout.write('\n')
        else:
            keySize = max(map(len, keys))
            formattedKeys = [k.ljust(keySize) for k in keys]
            for row in formattedRows:
                for i, field in enumerate(row):
                    fout.write('{0}: {1}\n'.format(formattedKeys[i], field))
                fout.write('\n')
