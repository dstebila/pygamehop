# the following built-ins and library functions should also work just fine
# although many return iterators/generators instead of tuples.  Syntactically this
# doesn't matter.  It can have problems with equality checking, though.  range(0,2) != (0,1)
# this can be solved by wrapping in tuple() like tuple(range(0,2)), which is the official python way
# to get a tuple from a generator/iterator.
# range()
# len()
# min()
# max()
# map()
# filter()
# itertools.*
# functools.reduce()
#
# some possible things to add:
# in(thelist, item)    x in L
# not_in(thelist, item) x not in L
# repeat(thelist, n)    thelist * n
# pre tuple() wrapped versions of built-in generator/iterator functions


def new_empty_list():
    return ()

def new_filled_list(length, fillitem):
    return tuple([ fillitem for i in range(0, length)])

def append_item(thelist, item):
    return thelist + (item,)

def set_item(thelist, index, item):
    l = list(thelist)
    l[index] = item
    return tuple(l)

def get_item(thelist, index):
    return thelist[index]

def index_of(thelist, item):
    return thelist.index(item)

def concat(l1, l2):
    return l1 + l2

def slice(thelist, start, end, step = 1):
    return thelist[start:end:step]
