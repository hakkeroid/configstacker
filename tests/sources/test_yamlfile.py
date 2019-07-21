# -*- coding: utf-8 -*-

import pytest

from configstacker import YAMLFile

try:
    import yaml
except ImportError:
    # skip all tests when yaml is not installed
    pytestmark = pytest.mark.skip(reason='Missing optional dependencies')


@pytest.fixture
def empty_yaml_file(tmpdir):
    path = tmpdir / 'config.yml'
    path.ensure()

    def loader(self):
        return yaml.safe_load(self.path.read())

    def writer(self, data):
        self.path.write(yaml.dump(data))

    test_file = pytest.helpers.DAL(path=path, _load_data=loader,
                                   _write_data=writer)
    return test_file


@pytest.fixture
def yaml_file(empty_yaml_file, data):
    empty_yaml_file.data = data
    yield empty_yaml_file


def test_read_empty_yaml_source(empty_yaml_file):
    config = YAMLFile(str(empty_yaml_file.path))

    assert len(config) == 0


def test_not_existing_file(tmpdir):
    path = tmpdir / 'config.yaml'

    config = YAMLFile(str(path))

    assert path.exists() is False

    config.a = 1

    assert path.read() == 'a: 1\n'


def test_lazy_read_yaml_source(yaml_file):
    config = YAMLFile(str(yaml_file.path))

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.d == {'e': 3}

    before = config.b.c

    expected = yaml_file.data
    expected['b']['c'] = 20
    yaml_file.data = expected

    after = config.b.c

    assert before == 2
    assert after == 20


def test_write_yaml_source(yaml_file):
    config = YAMLFile(str(yaml_file.path))
    expected = yaml_file.data
    expected['a'] = 10
    expected['b']['c'] = 20
    expected['b']['d']['e'] = 30

    assert config.a == 1
    assert config.b.c == 2
    assert config.b.d == {'e': 3}

    config.a = 10
    config.b.c = 20
    config.b.d.e = 30

    assert yaml_file.data == expected
