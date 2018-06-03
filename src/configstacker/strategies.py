# -*- coding: utf-8 -*-

"""Provide default merge strategies for convenience.

When working with stacked configurations there might be keys that occure
in multiple sources. By default the higher prioritized source will
shadow the lower prioritized key. This behavior can be changed with
these strategies.

All functions use ``next_`` as a paramter to prevent name collisions with
the builtin :func:`next`.

Attributes:

    EMPTY: Denote an empty value which removes the need to rely on
        :obj:`None` as a flow control value.
"""

__all__ = ['add', 'collect', 'merge', 'make_join', 'EMPTY']


class _Empty(object):
    pass


EMPTY = _Empty()


def add(previous, next_):
    """Summate the individual items of the same key from all sources.

    Args:
        previous: The result from the last summarization. If this is the
            first occurence of a key then this is :obj:`EMPTY`.

        next\\_: The value that was found in the currently iterated source.

    Returns:
        When `previous` is :obj:`EMPTY` it returns `next_`.

    Examples:
        >>> add(5, 3)
        8
    """
    if previous is EMPTY:
        return next_
    return previous + next_


def collect(previous, next_):
    """Collect items of the same key from all sources into a list.

    Args:
        previous: The collection of values from all previously iterated
            sources. If this is the first occurence of a key then this
            is :obj:`EMPTY`.
        next\\_: The value that was found in the currently iterated source.

    Returns:
        When `previous` is :obj:`EMPTY` it returns a list containing `next_`.

    Examples:
        >>> collect('a', 'b')
        ['a', 'b']
        >>> collect([1, 2], ['b', 'c'])
        [[1, 2], ['b', 'c']]
    """
    if previous is EMPTY:
        return [next_]
    return previous + [next_]


def merge(previous, next_):
    """Merge multiple lists or tuples into a single list or tuple.

    Args:
        previous: The result from the last merge. If this is the first
            occurence of a key then this is :obj:`EMPTY`.
        next\\_: The value that was found in the currently iterated source.

    Returns:
        When `previous` is :obj:`EMPTY` it returns `next_`.

    Examples:
        >>> merge([1, 2], [3, 4])
        [1, 2, 3, 4]
    """
    return add(previous, next_)


def make_join(separator=''):
    """Create a join-like function with the specified separator.

    Args:
        separator (str): This separator will be used to join consecutive
            values.

    The returned function has the following signature:

    Args:
        previous: The result from the last merge. If this is the
            first occurence of a key then this is :obj:`EMPTY`.
        next\\_: The value that was found in the currently
            iterated source.

    Returns:
        When `previous` is :obj:`EMPTY` it returns `next_`.

    Examples:
        >>> join = make_join('_')
        >>> join('a', 'b')
        'a_b'
        >>> join(EMPTY, 'b')
        'b'
    """
    def join(previous, next_):
        if previous is EMPTY:
            return next_
        return separator.join([previous, next_])
    return join
