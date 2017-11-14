# -*- coding: utf-8 -*-

import io

import pytest

from configstacker import (DictSource, Environment, INIFile, StackedConfig,
                           strategies)


def test_use_dictsource_on_empty_stacked_config():
    config = StackedConfig()

    assert config.dump() == {}


@pytest.mark.parametrize('source, error_type', [
    ({}, 'dict'),
    (None, 'NoneType'),
])
def test_raise_exception_on_wrong_source_types(source, error_type):
    with pytest.raises(ValueError) as exc_info:
        StackedConfig(source)

    assert "not '%s'" % error_type in str(exc_info)


def test_set_keychain():
    config = StackedConfig(
        DictSource({'a': {'b': {'c': 2}}}),
        keychain=('a', 'b')
    )

    assert config.dump() == {'c': 2}


def test_properly_return_none_values():
    config = StackedConfig(
        DictSource({'a': None})
    )

    assert config.a is None


def test_read_stacked_sources():
    config = StackedConfig(
        DictSource({'a': 1, 'b': {'c': 2}}),
        DictSource({'x': 6, 'b': {'y': 7, 'd': {'e': 8}}})
    )

    assert config.a == 1
    assert config.x == 6
    assert config.b.c == 2
    assert config.b.y == 7

    assert config['a'] == 1
    assert config['x'] == 6
    assert config['b'].c == 2
    assert config.b['y'] == 7
    assert config.b.d.e == 8


def test_read_complex_stacked_sources(monkeypatch):
    monkeypatch.setenv('MVP1_A', 1000)
    monkeypatch.setenv('MVP2_B_M_E', 4000)

    config = StackedConfig(
        Environment('MVP1_'),  # untyped shadowing
        DictSource({'a': 1, 'b': {'c': 2, 'e': 400}}),
        DictSource({'x': 6, 'b': {'y': 7, 'd': {'e': 8}}}),
        DictSource({'a': 100, 'b': {'m': {'e': 800}}}),     # shadowing
        DictSource({'x': 'x', 'b': {'y': 0.7, 'd': 800}}),  # type changing
        Environment('MVP2_'),  # untyped shadowing
    )

    assert config.a == 100
    assert config.x == 'x'       # changed int to str
    assert config.b.c == 2
    assert config.b.y == 0.7     # changed int to float
    assert config.b.d == 800     # changed subsection (dict) to single value
    assert config.b.e == 400     # 'e' should not be shadowed by other 'e'
    assert config.b.m.e == 4000  # shadowed by untyped but casted to type

    with pytest.raises(KeyError) as exc_info:
        config.b.x

    # config.b.d.e overrides a dict with a value
    with pytest.raises(AttributeError) as exc_info:
        config.b.d.e
    assert "no attribute 'e'" in str(exc_info.value)


def test_stacked_len():
    config = StackedConfig(
        DictSource({'a': 1, 'b': {'c': 2}}),
        DictSource({'x': 6, 'b': {'y': 7, 'd': {'e': 8}}})
    )

    assert len(config) == 3


def test_write_to_empty_sources():
    source1 = DictSource(default_for_missing={})
    source2 = DictSource()
    config = StackedConfig(source2, source1)

    config.a = 10
    config['b'].c = 20

    assert source1.a == 10
    assert source1.b.c == 20
    assert source2.dump() == {}


def test_write_stacked_source():
    source1 = DictSource({'a': 1, 'b': {'c': 2}})
    source2 = DictSource({'x': 6, 'b': {'y': 7, 'd': {'e': 8}}})
    config = StackedConfig(source1, source2)

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.y == 7

    config.a = 10
    config['x'] = 60
    config['b'].c = 20
    config.b['y'] = 70
    config.b['m'] = 'n'  # add new key
    config.b.d.e = 80

    assert config.a == 10
    assert config.x == 60
    assert config.b.c == 20
    assert config.b.y == 70
    assert config.b.m == 'n'
    assert config.b.d.e == 80

    assert source1.a == 10
    assert source1.b.c == 20

    assert source2.x == 60
    assert source2.b.y == 70
    assert source2.b.m == 'n'
    assert source2.b.d.e == 80


@pytest.mark.parametrize('key, message', (
    ('a', 'locked'),
    ('x', 'writable'),
))
def test_write_stacked_source_fails(key, message):
    source1 = DictSource({'a': 1, 'b': {'c': 2}}, readonly=True)
    config = StackedConfig(source1)

    with pytest.raises(TypeError) as exc_info:
        config[key] = 10

    assert message in str(exc_info.value)


def test_get_root():
    config = StackedConfig(
        DictSource({'x': 6, 'b': {'y': 7, 'd': {'e': 8}}})
    )

    assert config.b.d.get_root() == config


@pytest.mark.parametrize('readonly', (True, False))
def test_is_writable(readonly):
    config = StackedConfig(
        DictSource(readonly=readonly)
    )

    assert config.is_writable() is not readonly


def test_is_writable_in_low_priority_source():
    config = StackedConfig(
        DictSource(),
        DictSource(readonly=True)
    )

    assert config.is_writable() is True


@pytest.mark.parametrize('source, typed', [
    (DictSource(), True),
    (Environment('MYAPP'), False),
])
def test_is_typed(source, typed):
    config = StackedConfig(
        source
    )

    assert config.is_typed() is typed


def test_stacked_get():
    config = StackedConfig(
        DictSource({'a': 1, 'b': {'c': 2}}),
        DictSource({'x': 6, 'b': {'y': 7, 'd': {'e': 8}}})
    )

    assert config.get('a') == 1
    assert config.get('x') == 6
    assert config.get('b').get('c') == 2
    assert config.get('b').get('y') == 7
    assert config.get('nonexisting') is None
    assert config.get('nonexisting', 'default') == 'default'
    assert 'nonexisting' not in config


def test_source_keys():
    config = StackedConfig(
        DictSource({'a': 1, 'b': {'c': 2}}),
        DictSource({'x': 6, 'b': {'y': 7, 'd': {'e': 8}}})
    )

    keys = list(config.b.keys())
    assert keys == ['c', 'd', 'y']


def test_source_values():
    config = StackedConfig(
        DictSource({'a': 1, 'b': {'c': 2}}),
        DictSource({'x': 6, 'b': {'y': 7, 'd': {'e': 8}}})
    )

    values = list(config.b.values())
    assert values == [2, config.b.d, 7]


def test_source_items(monkeypatch):
    monkeypatch.setenv('MVP_A', 10)
    config = StackedConfig(
        DictSource({'a': 1, 'b': {'c': 2}}),
        Environment('MVP'),
        DictSource({'x': 6, 'b': {'y': 7}})
    )

    items = list(config.items())
    assert items == [('a', 10), ('b', config.b), ('x', 6)]

    items = list(config.b.items())
    assert items == [('c', 2), ('y', 7)]


@pytest.mark.parametrize('reverse, values', [
    (False, (1000, 200)),
    (True, (1, 20)),
])
def test_reverse_source_order(reverse, values):
    sources = [
        DictSource({'a': 1, 'b': {}}),
        DictSource({'a': 10, 'b': {'c': 20}}),
        DictSource({'a': 100, 'b': {'c': 200}}),
        DictSource({'a': 1000, 'b': {}}),
    ]

    config = StackedConfig(*sources, reverse=reverse)

    assert config.a == values[0]
    assert config.b.c == values[1]


@pytest.mark.xfail
@pytest.mark.parametrize('reverse', (True, False))
def test_source_items_prevent_shadowing_between_subsections_and_values(reverse):
    sources = [
        DictSource({'a': 1, 'b': {'c': 2}}),
        DictSource({'x': 6, 'b': 5}),
    ]
    config = StackedConfig(*sources, reverse=reverse)

    with pytest.raises(ValueError) as exc_info:
        list(config.items())

    assert "conflicts" in str(exc_info.value)


def test_source_items_with_strategies_and_untyped_source(monkeypatch):
    monkeypatch.setenv('MVP_A', 100)
    untyped_source = io.StringIO(pytest.helpers.unindent(u"""
        [__root__]
        a=1000
    """))

    config = StackedConfig(
        Environment('MVP'),  # last source still needs a typed source
        DictSource({'a': 1, 'x': [5, 6], 'b': {'c': 2, 'd': [3, 4]}}),
        DictSource({'a': 10, 'x': [50, 60], 'b': {'c': 20, 'd': [30, 40]}}),
        INIFile(untyped_source),
        strategy_map={
            'a': strategies.add,
            'x': strategies.collect,  # keep lists intact
            'c': strategies.collect,  # collect values into list
            'd': strategies.merge,    # merge lists
        }
    )

    items = list(config.items())
    assert items == [('a', 1111),
                     ('b', config.b),
                     ('x', [[50, 60], [5, 6]])]

    items = list(config.b.items())
    assert items == [('c', [20, 2]),
                     ('d', [30, 40, 3, 4])]


def test_stacked_dump():
    config = StackedConfig(
        DictSource({'a': 1, 'b': {'c': 2}}),
        DictSource({'a': '10'}),
        DictSource({'x': 6, 'b': {'y': 7}})
    )

    assert config.dump() == {'a': '10', 'b': {'c': 2, 'y': 7}, 'x': 6}


def test_stacked_setdefault():
    source1 = DictSource({'a': 1, 'b': {'c': 2}})
    source2 = DictSource({'x': 6, 'b': {'y': 7}})
    config = StackedConfig(source1, source2)

    assert config.setdefault('a', 10) == 1
    assert config.setdefault('nonexisting', 10) == 10
    assert config.nonexisting == 10
    assert 'nonexisting' in source2

    assert config.b.setdefault('nonexisting', 20) == 20
    assert config.b.nonexisting == 20
    assert 'nonexisting' in source2.b


@pytest.mark.parametrize('container', [
    dict, DictSource
])
def test_stacked_simple_update(container):
    source1 = DictSource({'a': 1, 'b': {'c': 2}})
    source2 = DictSource({'x': 6, 'b': {'y': 7}})
    config = StackedConfig(source1, source2)

    data1 = container({'a': 10, 'x': 60})
    data2 = container({'c': 20})
    data3 = container({'y': 70})

    config.update(data1)
    config.b.update(data2, data3)

    assert config.a == 10
    assert config.x == 60
    assert config.b.c == 20
    assert config.b.y == 70

    assert source1.a == 10
    assert source1.b.c == 20

    assert source2.x == 60
    assert source2.b.y == 70


def test_stacked_config_with_untyped_source():
    typed_source1 = {'x': 5, 'b': {'y': 6}}
    typed_source2 = {'a': 1, 'b': {'c': 2}}
    untyped_source1 = io.StringIO(pytest.helpers.unindent(u"""
        [__root__]
        a=11
    """))
    untyped_source2 = io.StringIO(pytest.helpers.unindent(u"""
        [__root__]
        a=10
        x=50

        [b]
        c=20
        y=60

        [b.d]
        e=30
    """))
    typed1 = DictSource(typed_source1)
    typed2 = DictSource(typed_source2)
    untyped1 = INIFile(untyped_source1)
    untyped2 = INIFile(untyped_source2, subsection_token='.')
    config = StackedConfig(typed1, typed2, untyped1, untyped2)

    assert typed1.x == 5
    assert typed1.b.y == 6

    assert typed2.a == 1
    assert typed2.b.c == 2
    with pytest.raises(KeyError):
        typed2.b.d.e

    assert untyped1.a == '11'

    assert untyped2.a == '10'
    assert untyped2.b.c == '20'
    assert untyped2.b.d.e == '30'

    assert config.a == 10    # found in first typed source
    assert config.x == 50    # found in second typed source
    assert config.b.c == 20
    assert config.b.y == 60
    assert config.b.d.e == '30'


def test_stacked_config_with_type_conversions():
    typed_source1 = {
        'a': 1,
        'b': 3.0,
        'c': 4+5j,
        'd': 'some string',
        'e': u'some unicode',
        'f': True,
        'g': False,
        'h': False,
        'i': True,
        'j': [1, 2],
        'k': (1, 2),
        'l': set([1, 2]),
    }
    untyped_source1 = io.StringIO(pytest.helpers.unindent(u"""
        [__root__]
        a=10
        b=20.01
        c=5+6j
        d=some other string
        e=some other unicode
        f=false
        g=True
        h=yes
        i=nope
        j=3, 4
        k=3, 4
        l=3, 4
    """))
    typed1 = DictSource(typed_source1)
    untyped1 = INIFile(untyped_source1)
    config = StackedConfig(typed1, untyped1)

    assert config.a == 10
    assert config.b == 20.01
    assert config.c == 5+6j
    assert config.d == 'some other string'
    assert config.e == u'some other unicode'
    assert config.f is False
    assert config.g is True
    assert config.h == True
    assert config.i == "nope"
    # the individual values cannot be converted
    # as we do not know their intended type
    assert config.j == ['3', '4']
    assert config.k == ('3', '4')
    assert config.l == set(['3', '4'])


def test_stacked_config_with_untyped_source_and_custom_converters():
    typed = DictSource({'a': 1})
    untyped = INIFile(io.StringIO(pytest.helpers.unindent(u"""
        [__root__]
        a=11
    """)))
    converter_map = {
        'a': (lambda v: v*2, lambda v: v/2),
    }

    config = StackedConfig(typed, untyped, converter_map=converter_map)

    assert config.a == 22


def test_read_stacked_sources_with_strategies():
    config = StackedConfig(
        DictSource({'a': 1, 'x': [5, 6], 'b': {'c': 2, 'd': [3, 4]}}),
        DictSource({'a': 10, 'x': [50, 60], 'b': {'c': 20, 'd': [30, 40]}}),
        strategy_map={
            'a': strategies.add,
            'x': strategies.collect,  # keep lists intact
            'c': strategies.collect,  # collect values into list
            'd': strategies.merge,    # merge lists
        }
    )

    assert config.a == 11
    assert config.x == [[50, 60], [5, 6]]
    assert config.b.c == [20, 2]
    assert config.b.d == [30, 40, 3, 4]


def test_read_stacked_sources_with_strategies_and_untyped_sources(monkeypatch):
    monkeypatch.setenv('MVP_A', 100)
    untyped_source = io.StringIO(pytest.helpers.unindent(u"""
        [__root__]
        a=1000
    """))

    config = StackedConfig(
        Environment('MVP'),  # last source still needs a typed source
        DictSource({'a': 1, 'x': [5, 6], 'b': {'c': 2, 'd': [3, 4]}}),
        DictSource({'a': 10, 'x': [50, 60], 'b': {'c': 20, 'd': [30, 40]}}),
        INIFile(untyped_source),
        strategy_map={
            'a': strategies.add,
            'x': strategies.collect,  # keep lists intact
            'c': strategies.collect,  # collect values into list
            'd': strategies.merge,    # merge lists
        }
    )

    assert config.a == 1111
    assert config.x == [[50, 60], [5, 6]]
    assert config.b.c == [20, 2]
    assert config.b.d == [30, 40, 3, 4]


def test_read_stacked_sources_with_strategies_for_none_values():
    config = StackedConfig(
        DictSource({'a': None}),
        DictSource({'a': None}),
        strategy_map={
            'a': strategies.collect,
        }
    )

    result = [None, None]

    assert config.a == result
    assert list(config.items()) == [('a', result)]


def test_read_stacked_sources_with_joining_strategy():
    source1 = DictSource({'path': '/path/to/default/file'})
    source2 = DictSource({'path': '/path/to/user/file'})

    config = StackedConfig(
        source1,
        source2,
        strategy_map={
            'path': strategies.make_join(separator=':')
        }
    )

    assert config.path == '/path/to/user/file:/path/to/default/file'


def test_expose_sources_for_manipulation():
    source1 = DictSource({'a': 1, 'b': {'c': 2}})
    source2 = DictSource({'a': 10, 'b': {'c': 20}})
    source3 = DictSource({'x': 6, 'b': {'y': 7}})
    config = StackedConfig()

    assert config.dump() == {}

    config.source_list.append(source1)
    assert config == source1

    config.source_list.append(source2)
    assert config == source2

    config.source_list.insert(0, source3)
    assert config.dump() == {'a': 10, 'b': {'c': 20, 'y': 7}, 'x': 6}


@pytest.fixture
def mytype_config():
    class MyType:
        def __init__(self, c):
            self.c = c

    def load_mytype(config):
        return MyType(config.c)

    def unload_mytype(mytype):
        return {'c': mytype.c}

    data = {'a': {'b': {'c': 1}}}
    types = {
        'b': (load_mytype, unload_mytype)
    }

    config = StackedConfig(
        DictSource(data),
        DictSource(data),
        converter_map=types,
    )

    return MyType, data, config


def test_read_source_with_complex_custom_converters(mytype_config):
    MyType, data, config = mytype_config

    mytype = MyType(1)

    assert isinstance(config, StackedConfig)
    assert isinstance(config.a.b, MyType)

    assert config.a.b.c == mytype.c

    dumped = config.dump()

    assert dumped['a']['b'].c == mytype.c
    assert isinstance(dumped['a']['b'], MyType)


def test_write_source_with_complex_custom_converters(mytype_config):
    MyType, data, config = mytype_config

    mytype = MyType(10)
    data['a']['b']['c'] = 10

    config.a.b = mytype

    assert isinstance(config, StackedConfig)
    assert isinstance(config.a.b, MyType)

    assert config.a.b.c == mytype.c

    dumped = config.dump()

    assert dumped['a']['b'].c == mytype.c
    assert isinstance(dumped['a']['b'], MyType)
