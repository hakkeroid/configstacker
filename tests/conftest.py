# -*- coding: utf-8 -*-

import functools
import textwrap

import pytest

pytest_plugins = ['helpers_namespace']


@pytest.fixture
def data():
    return {
        'a': 1,
        'b': {
            'c': 2,
            'd': {
                'e': 3
            }
        }
    }


@pytest.fixture
def inimaker(tmpdir):
    def write(text, filename='config{id}.ini'):
        """Creates a temporary ini file

        Args:
            text (str): The content of the INI file.
            filename (str): Specifies the name of the INI file.
                By default this is 'config.ini'.
        """
        write.num_files += 1
        unindented = textwrap.dedent(text)
        path = tmpdir / filename.format(id=write.num_files)
        path.write(unindented)
        return str(path)
    # Provide state to function for subsequent calls. Will be reset
    # after the test run.
    write.num_files = 0
    return write


@pytest.helpers.register
class DAL(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @property
    def data(self):
        return self._load_data(self)

    @data.setter
    def data(self, data):
        self._write_data(self, data)


@pytest.helpers.register
def inspector(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        return fn(*args, **kwargs)
    wrapper.calls = 0
    wrapper.args = None
    wrapper.kwargs = None
    return wrapper
