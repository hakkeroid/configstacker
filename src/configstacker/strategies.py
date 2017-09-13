# -*- coding: utf-8 -*-

__all__ = ['add', 'collect', 'merge', 'make_join', 'EMPTY']


class _Empty(object):
    pass

#: Denote an empty value so that "None" stays available as a normal
#: value.
EMPTY = _Empty()


def add(previous, next_):
    if previous is EMPTY:
        return next_
    return previous + next_


def collect(previous, next_):
    if previous is EMPTY:
        return [next_]
    return previous + [next_]


def merge(previous, next_):
    return add(previous, next_)


def make_join(separator=''):
    def join(previous, next_):
        if previous is EMPTY:
            return next_
        return separator.join([previous, next_])
    return join
