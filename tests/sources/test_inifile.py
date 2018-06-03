# -*- coding: utf-8 -*-

import io

import pytest

from configstacker import INIFile


@pytest.fixture
def ini_file(inimaker):
    path = inimaker(u"""
        [__root__]
        a=1

        [b]
        c=2

        [b.d]
        e=%(interpolated)s
        interpolated=3

        [b/d/f]
        g=4
    """)

    return path


def test_read_ini_source(ini_file):
    config = INIFile(ini_file)

    assert config.a == '1'
    assert config.b.c == '2'
    assert config['b.d'].e == '3'
    assert config['b/d/f'].g == '4'


def test_read_ini_source_from_file_object(ini_file):
    with open(ini_file) as fh:
        config = INIFile(fh)

    assert config.a == '1'
    assert config.b.c == '2'
    assert config['b.d'].e == '3'
    assert config['b/d/f'].g == '4'


def test_read_ini_source_with_subsections(ini_file):
    config = INIFile(ini_file, subsection_token='.')

    assert config.a == '1'
    assert config.b.c == '2'
    assert config.b.d.e == '3'
    assert config['b/d/f'].g == '4'


def test_write_ini_source(ini_file):
    config = INIFile(ini_file, subsection_token='.', auto_subsection=True)

    assert config.a == '1'
    assert config.b.c == '2'
    assert config.b.d.e == '3'
    assert config['b/d/f'].g == '4'

    config.a = 10
    config.b.c = 20
    config.b.d.e = 30
    config['b/d/f'].g = 40
    config.x.y.z = 50

    assert 'a = 10' in open(ini_file).read()


def test_change_root_name(inimaker):
    config = INIFile(inimaker(u"""
        [myroot]
        a=1

        [b]
        c=2

        [b.d]
        e=%(interpolated)s
        interpolated=3

        [b/d/f]
        g=4
    """), root_section='myroot')

    assert config.a == '1'
    assert config.b.c == '2'
    assert config['b.d'].e == '3'
    assert config['b/d/f'].g == '4'
