# -*- coding: utf-8 -*-

import pytest

from configstacker.sources import DictSource
from configstacker.stacker import SourceIterator


@pytest.fixture
def sources():
    config1 = DictSource({'a': 1, 'b': {'c': 2, 'd': {'e': 3}}})
    config2 = DictSource({'m': 1, 'n': {'o': 2, 'p': {'q': 3}}})
    return [config1, config2]


def test_init_empty_source_list():
    sources = SourceIterator()

    assert list(sources) == []
    assert len(sources) == 0


@pytest.mark.parametrize('source, error', [
    ('a source', "not 'str'"),
    (None, "not 'NoneType'")
])
def test_adding_invalid_source_fails(source, error):
    with pytest.raises(ValueError) as exc_info:
        SourceIterator(source)

    assert error in str(exc_info.value)


def test_calling_with_invalid_parameters():
    with pytest.raises(ValueError) as exc_info:
        SourceIterator(unknown=False)

    assert "{'unknown': False}" in str(exc_info.value)


def test_iterate_sources():
    source1 = DictSource({'a': 1, 'b': {'c': 2}})
    source2 = DictSource({'m': 10, 'b': {'o': 20}})

    sources = SourceIterator(source1, source2)

    assert list(sources) == [source1, source2]


def test_iterate_sources_with_keychain():
    source1 = DictSource({'a': 1, 'b': {'c': 2}})
    source2 = DictSource({'m': 10, 'b': {'o': 20}})
    subsource1 = DictSource({'c': 2})
    subsource2 = DictSource({'o': 20})

    sources = SourceIterator(source1, source2, keychain=['b'])

    assert list(sources) == [subsource1, subsource2]


def test_add_source_after_instantiation():
    source1 = DictSource({'a': 1, 'b': {'c': 2}})
    source2 = DictSource({'m': 10, 'b': {'o': 20}})

    sources = SourceIterator(source1)
    sources.append(source2)

    assert list(sources) == [source1, source2]


def test_remove_source_after_instantiation():
    source1 = DictSource({'a': 1, 'b': {'c': 2}})
    source2 = DictSource({'m': 10, 'b': {'o': 20}})

    sources = SourceIterator(source1, source2)
    sources.remove(source1)

    assert list(sources) == [source2]

    del sources[0]

    assert list(sources) == []


def test_change_source_after_instantiation():
    source1 = DictSource({'a': 1, 'b': {'c': 2}})
    source2 = DictSource({'m': 10, 'b': {'o': 20}})
    updated = DictSource({'x': 100, 'b': {'y': 200}})

    sources = SourceIterator(source1, source2)
    sources[0] = updated

    assert list(sources) == [updated, source2]
