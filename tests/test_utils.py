# -*- coding: utf-8 -*-

from configstacker import utils


def test_make_subdicts():
    base = {}
    subkeys = ['a', 'b', 'c']

    last = utils.make_subdicts(base, subkeys)

    assert base == {'a': {'b': {'c': {}}}}
    assert last == {}
