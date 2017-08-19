# -*- coding: utf-8 -*-

import os

import six

from . import base
from .. import utils

__all__ = ['Environment']


class Environment(base.Source):
    """Reads environment variables"""

    _is_typed = False

    def __init__(self, prefix=None, subsection_token='_', **kwargs):
        super(Environment, self).__init__(**kwargs)
        self._prefix = prefix
        self.subsection_token = subsection_token

    def _read(self):
        data = {}
        for env_key, value in _iter_environ(self._prefix):
            tokens = env_key.lower().split(self.subsection_token)
            keychain = tokens[1:-1]
            key = tokens[-1]
            subdict = utils.make_subdicts(data, keychain)
            subdict[key] = value

        return data

    def _write(self, data):
        def _write(section, keychain):
            for key, value in six.iteritems(section):
                next_keychain = keychain + [key]
                if isinstance(value, dict):
                    _write(value, next_keychain)
                else:
                    full_key = self.subsection_token.join(next_keychain)
                    os.environ[full_key.upper()] = str(value)

        _write(data, [self._prefix])


def _iter_environ(prefix):
    prefix_ = prefix.lower()
    for key, value in six.iteritems(os.environ):
        if key.lower().startswith(prefix_):
            yield key, value
