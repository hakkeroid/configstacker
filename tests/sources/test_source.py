# -*- coding: utf-8 -*-

import datetime

import pytest

from configstacker import DictSource, Source, converters


def test_enforce_read_method():
    with pytest.raises(NotImplementedError) as exc_info:
        class MySource(Source):
            pass

    assert 'required "_read"' in str(exc_info.value)


def test_read_dict_source():
    data = {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}}
    config = DictSource(data)

    # only count toplevel keys
    assert len(config) == 2

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.d == {'e': 3}

    assert config['a'] == 1
    assert config['b'].c == 2
    assert config.b['d'] == {'e': 3}

    # test lazy read
    data['a'] = 10
    data['b']['c'] = 20
    data['b']['d']['e'] = 30

    assert config.a == 10
    assert config.b.c == 20
    assert config.b.d == {'e': 30}


def test_write_dict_source():
    data = {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}}
    config = DictSource(data)

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.d == {'e': 3}

    config.a = 10
    config.b.c = 20
    del config.b.d.e

    assert config.a == 10
    assert config.b.c == 20
    with pytest.raises(KeyError):
        config.b.d.e


def test_prevent_writing_to_readonly_source():
    class ReadonlySource(Source):
        def _read(self):
            return {}

    config = ReadonlySource()

    with pytest.raises(TypeError) as exc_info:
        config.a = 10

    assert 'read-only source' in str(exc_info.value)


def test_prevent_writing_to_locked_source():
    data = {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}}
    config = DictSource(data, readonly=True)

    with pytest.raises(TypeError) as exc_info:
        config.a = 10

    assert 'locked' in str(exc_info.value)

    with pytest.raises(TypeError) as exc_info:
        config.b.c = 20

    assert 'locked' in str(exc_info.value)


def test_source_get():
    config = DictSource({'a': 1})

    assert config.get('a') == 1
    assert config.get('nonexisting') is None
    assert config.get('nonexisting', 'default') == 'default'
    assert 'nonexisting' not in config


def test_source_items():
    data = {'a': {'b': 1}}
    config = DictSource(data)

    items = [i for i in config.a.items()]
    assert items == [('b', 1)]


def test_source_items_with_converters():
    data = {'a': {'b': 1}}
    converter_list = [
        ('b', lambda v: 2*v, lambda v: v/2),
    ]
    config = DictSource(data, converters=converter_list)

    items = [i for i in config.a.items()]
    assert items == [('b', 2)]


@pytest.mark.parametrize('converter,value,customized,reset', [
    (converters.bools('a'), 'True', True, 'True'),
    (converters.bools('a'), 'false', False, 'False'),
    (converters.bools('a'), 'yes', True, 'True'),
    (converters.bools('a'), 'No', False, 'False'),
    (converters.bools('a'), '1', True, 'True'),

    (converters.dates('a'), '2017-10-22',
        datetime.date(2017, 10, 22), '2017-10-22'),

    (converters.dates('a', '%d.%m.%Y'), '22.10.2017',
        datetime.date(2017, 10, 22), '22.10.2017'),

    # use default strict format
    (converters.datetimes('a'), '2017-10-22T10:00:20',
        datetime.datetime(2017, 10, 22, 10, 0, 20), '2017-10-22T10:00:20'),

    # use different format that allows empty values
    (converters.datetimes('a', '%Y-%m'), '2017-10',
        datetime.datetime(2017, 10, 1, 0, 0, 0), '2017-10'),
])
def test_builtin_converters(converter, value, customized, reset):
    data = {'a': value}
    config = DictSource(data, converters=[converter])

    assert config.a == customized

    del config.a
    config.a = customized

    assert config._data['a'] == reset


def test_source_keys():
    data = {'a': {'b': 1}}
    config = DictSource(data)

    items = [i for i in config.a.keys()]
    assert items == ['b']


def test_source_values():
    data = {'a': {'b': 1}}
    config = DictSource(data)

    items = [i for i in config.a.values()]
    assert items == [1]


def test_source_values_with_converters():
    data = {'a': {'b': 1}}
    converter_list = [
        ('b', lambda v: 2*v, lambda v: v/2),
    ]
    config = DictSource(data, converters=converter_list)

    items = [i for i in config.a.values()]
    assert items == [2]


def test_source_setdefault():
    config = DictSource({'a': 1})

    assert config.setdefault('a', 10) == 1
    assert config.setdefault('nonexisting', 10) == 10
    assert config.nonexisting == 10


def test_source_setdefault_as_subsection():
    config = DictSource()

    with pytest.raises(KeyError):
        config.a.b = 1

    config.setdefault('a', {}).b = 1

    assert config.a.b == 1


def test_set_missing_key_to_default_value():
    config = DictSource(auto_subsection=True)

    config.a.b = 1
    config['x'].y = 2

    assert config.a.b == 1
    assert config.x.y == 2


@pytest.mark.parametrize('container', [
    dict, DictSource
])
def test_source_update(container):
    source = {'a': {'b': 1}}
    config = DictSource(source)

    data1 = {'x': 4}
    data2 = container({'y': 5})
    expected = {'a': {'b': 1, 'x': 4, 'y': 5}}

    config.a.update(data1)
    config.a.update(data2)

    assert config == expected


def test_read_source_with_converters():
    data = {'a': 1, 'b': {'c': 2}}
    converter_list = [
        ('a', str, int),
        ('c', lambda v: 2*v, lambda v: v/2),
    ]
    config = DictSource(data, converters=converter_list)

    assert config.a == '1'
    assert config.b.c == 4

    assert config.dump() == {'a': '1', 'b': {'c': 4}}


def test_write_source_with_converters():
    data = {'a': 1, 'b': {'c': 2}}
    converter_list = [
        ('a', str, int),
        ('c', lambda v: 2*v, lambda v: v/2),
    ]
    config = DictSource(data, converters=converter_list)

    config.a = '1'
    config.b.c = 4

    assert config._data == data


@pytest.fixture
def mytype_config():
    class MyType:
        def __init__(self, b):
            self.b = b

    def load_mytype(config):
        return MyType(config.b)

    def unload_mytype(mytype):
        return {'b': mytype.b}

    data = {'a': {'b': 1}}
    converter_list = [
        ('a', load_mytype, unload_mytype),
    ]

    return MyType, data, DictSource(data, converters=converter_list)


def test_read_source_with_complex_converters(mytype_config):
    MyType, data, config = mytype_config

    mytype = MyType(1)

    assert isinstance(config, DictSource)
    assert isinstance(config.a, MyType)

    assert config.a.b == mytype.b

    dumped = config.dump()

    assert dumped['a'].b == mytype.b
    assert isinstance(dumped['a'], MyType)


def test_write_source_with_complex_converters(mytype_config):
    MyType, data, config = mytype_config

    mytype = MyType(10)
    data['a']['b'] = 10

    config.a = mytype

    assert config.a.b == mytype.b

    dumped = config.dump()

    assert dumped['a'].b == mytype.b
    assert isinstance(dumped['a'], MyType)


def test_read_source_with_wildcard_converters():
    data = {'a': {'b': 1,
                  'c': 2},
            'x': {'b': 10,
                  'c': 20}}
    converter_list = [
        ('a.*', lambda v: 2*v, lambda v: v/2),
        ('*.c', lambda v: 3*v, lambda v: v/3),
    ]
    config = DictSource(data, converters=converter_list)

    # converted by first converter a.*
    assert config.a.b == 2
    # fits both converters, however first one is used due to higher priority
    assert config.a.c == 4
    # not converted because no converter fits
    assert config.x.b == 10
    # converted by second converter *.c
    assert config.x.c == 60


def test_read_cached_dict_source():
    data = {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}}
    config = DictSource(data, cached=True)

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.d == {'e': 3}

    # test cached access
    data['a'] = 10
    data['b']['c'] = 20
    data['b']['d']['e'] = 30

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.d == {'e': 3}

    config.clear_cache()

    assert config.a == 10
    assert config.b.c == 20
    assert config.b.d == {'e': 30}


def test_write_cached_dict_source():
    config = DictSource({}, cached=True)

    config.a = 1
    config.b = {}
    config.b.c = 2
    config.b.d = {}
    config.b.d.e = 3

    assert config._data == {}

    config.write_cache()

    assert config._data == {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}}


def test_get_source_root():
    data = {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}}
    config = DictSource(data, cached=True)

    assert config.b.d.get_root() is config
