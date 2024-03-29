# -*- coding: utf-8 -*-

import pytest

from configstacker import DictSource
from configstacker.sources.stacker import SourceList


@pytest.fixture
def sources():
    config1 = DictSource({'a': 1, 'b': {'c': 2, 'd': {'e': 3}}})
    config2 = DictSource({'m': 1, 'n': {'o': 2, 'p': {'q': 3}}})
    return [config1, config2]


def test_init_empty_source_list():
    sources = SourceList()

    assert list(sources) == []
    assert len(sources) == 0


@pytest.mark.parametrize('source, error', [
    ('a source', "not 'str'"),
    (None, "not 'NoneType'")
])
def test_adding_invalid_source_fails(source, error):
    with pytest.raises(ValueError) as exc_info:
        SourceList(source)

    assert error in str(exc_info.value)


def test_calling_with_invalid_parameters():
    with pytest.raises(ValueError) as exc_info:
        SourceList(unknown=False)

    assert "{'unknown': False}" in str(exc_info.value)


def test_iterate_sources():
    source1 = DictSource({'a': 1, 'b': {'c': 2}})
    source2 = DictSource({'m': 10, 'b': {'o': 20}})

    sources = SourceList(source1, source2)

    # sources will be returned reversed to start with the highest
    # priority
    assert list(sources) == [source2, source1]


def test_iterate_sources_with_keychain():
    source1 = DictSource({'a': 1, 'b': {'c': 2}})
    source2 = DictSource({'m': 10, 'b': {'o': 20}})
    subsource1 = DictSource({'c': 2})
    subsource2 = DictSource({'o': 20})

    sources = SourceList(source1, source2, keychain=['b'])

    assert list(sources) == [subsource2, subsource1]


def test_add_source_after_instantiation():
    source1 = DictSource({'a': 1, 'b': {'c': 2}})
    source2 = DictSource({'m': 10, 'b': {'o': 20}})

    sources = SourceList(source1)
    sources.append(source2)

    assert list(sources) == [source2, source1]


def test_remove_source_after_instantiation():
    source1 = DictSource({'a': 1, 'b': {'c': 2}})
    source2 = DictSource({'m': 10, 'b': {'o': 20}})

    sources = SourceList(source1, source2)
    sources.remove(source1)

    assert list(sources) == [source2]

    del sources[0]

    assert list(sources) == []


def test_change_source_after_instantiation():
    source1 = DictSource({'a': 1, 'b': {'c': 2}})
    source2 = DictSource({'m': 10, 'b': {'o': 20}})
    updated = DictSource({'x': 100, 'b': {'y': 200}})

    sources = SourceList(source1, source2)
    sources[0] = updated

    assert list(sources) == [source2, updated]


def test_prevent_adding_invalid_sources_after_instantiation():
    source1 = DictSource({'a': 1, 'b': {'c': 2}})
    updated = "Invalid Source"

    sources = SourceList(source1)

    with pytest.raises(ValueError) as exc_info:
        sources.append(updated)
    assert 'must be a subclass' in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        sources.insert(0, updated)
    assert 'must be a subclass' in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        sources[0] = updated
    assert 'must be a subclass' in str(exc_info.value)


def test_prevent_changes_to_source_of_subconfig():
    source1 = DictSource({'a': 1, 'b': {'c': 2}})
    source2 = DictSource({'m': 10, 'b': {'o': 20}})
    updated = DictSource({'x': 100, 'b': {'y': 200}})

    sources = SourceList(source1, source2, keychain=['b'])

    with pytest.raises(TypeError) as exc_info:
        sources.append(updated)
    assert 'cannot be mutated' in str(exc_info.value)

    with pytest.raises(TypeError) as exc_info:
        sources.insert(0, updated)
    assert 'cannot be mutated' in str(exc_info.value)

    with pytest.raises(TypeError) as exc_info:
        sources[0] = updated
    assert 'cannot be mutated' in str(exc_info.value)
