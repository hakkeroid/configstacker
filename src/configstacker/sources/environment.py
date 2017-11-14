# -*- coding: utf-8 -*-

import os

import six

from . import base
from .. import utils

__all__ = ['Environment']


class Environment(base.Source):
    """Reads environment variables"""

    class Meta:
        is_typed = False

    def __init__(self, prefix, subsection_token='_', **kwargs):
        super(Environment, self).__init__(**kwargs)
        self._prefix = prefix
        self.subsection_token = subsection_token

    def _read(self):
        data = {}
        for keys, value in _iter_environ(self._prefix):
            keychain = keys.lower().split(self.subsection_token)

            # do not remove prefix when it is an empty string
            # which is only used for accessing system environment
            # variables.
            if self._prefix:
                keychain.pop(0)

            # separate last key which is a leaf
            key = keychain.pop()

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
