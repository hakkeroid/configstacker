# -*- coding: utf-8 -*-

import pytest

from configstacker import Environment


def test_read_environment_source(monkeypatch):
    monkeypatch.setenv('MVP_A', 1)
    monkeypatch.setenv('MVP_B_C', 2)
    monkeypatch.setenv('MVP_B_D_E', 3)
    config = Environment(prefix='MVP')

    assert config.a == '1'
    assert config.b.c == '2'
    assert config.b.d == {'e': '3'}


def test_read_environment_source_with_empty_prefix(monkeypatch):
    monkeypatch.setenv('MVP_A', 1)
    monkeypatch.setenv('MVP_B_C', 2)
    monkeypatch.setenv('MVP_B_D_E', 3)
    config = Environment('')

    assert 'path' in config
    assert 'pythonhashseed' in config

    assert 'tox' in config.virtual.env
    assert 'empty_prefix' in config.pytest.current.test

    assert config.mvp.a == '1'
    assert config.mvp.b.c == '2'
    assert config.mvp.b.d == {'e': '3'}


def test_write_environment_fails(monkeypatch):
    monkeypatch.setenv('MVP_A', 1)
    config = Environment(prefix='MVP', readonly=True)

    with pytest.raises(TypeError) as exc_info:
        config.a = 10
    assert 'locked' in str(exc_info.value)


def test_write_environment_source(monkeypatch):
    monkeypatch.setenv('MVP_A', 1)
    monkeypatch.setenv('MVP_B_C', 2)
    monkeypatch.setenv('MVP_B_D_E', 3)
    config = Environment(prefix='MVP')

    config.a = 10
    config.b.c = '20'
    config.b['d'].e = '30'

    assert config.a == '10'  # looses typing information
    assert config.b.c == '20'
    assert config.b.d == {'e': '30'}
