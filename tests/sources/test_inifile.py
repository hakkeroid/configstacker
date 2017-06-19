# -*- coding: utf-8 -*-

import io

import pytest

from configstacker.sources import INIFile


@pytest.fixture
def ini_file(tmpdir):
    path = tmpdir / 'config.ini'
    path.write(pytest.helpers.unindent(u"""
        [__root__]
        a=1

        [b]
        c=2

        [b.d]
        e=%(interpolated)s
        interpolated=3

        [b/d/f]
        g=4
    """))

    return path


def test_read_ini_source(ini_file):
    config = INIFile(str(ini_file))

    assert config.a == '1'
    assert config.b.c == '2'
    assert config['b.d'].e == '3'
    assert config['b/d/f'].g == '4'


def test_read_ini_source_from_file_object(ini_file):
    with open(str(ini_file)) as fh:
        config = INIFile(fh)

    assert config.a == '1'
    assert config.b.c == '2'
    assert config['b.d'].e == '3'
    assert config['b/d/f'].g == '4'


def test_read_ini_source_with_subsections(ini_file):
    config = INIFile(str(ini_file), subsection_token='.')

    assert config.a == '1'
    assert config.b.c == '2'
    assert config.b.d.e == '3'
    assert config['b/d/f'].g == '4'
