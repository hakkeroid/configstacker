# -*- coding: utf-8 -*-

import os

import six

from .. import utils
from . import base

__all__ = ['Environment']


class Environment(base.Source):
    """Source loader for environment variables.

    Environment variables are untyped sources. If you need typed data
    you either have to use :any:`configstacker.StackedConfig` with
    another source that is typed or add a :any:`Converter` which takes
    care of all type :ref:`conversions <advanced-converters>`.
    Environment variables are writable by default.

    Args:
        prefix (str): A string that prefixes all relevant environment
            variables. Configstacker will only lookup variables starting
            with that prefix.

        subsection_token (str, optional): Will be used to split
            a variable name into subsections. Defaults to ``_``.

        kwargs: See :any:`Source` for additional options.

    For the next example assume the environment variables are set up as
    following::

        os.environ['APP1_SIMPLE_INT'] = '10'
        os.environ['APP2|SIMPLE_INT'] = '20'

    Examples:
        >>> from configstacker import Environment
        >>> config = Environment('APP1', subsection_token='_')
        >>> config.simple.int  # "int" was interpreted as a subsection of "simple"
        '10'
        >>> config.simple_int  # raises a KeyError as "simple_int" was split up
        ...
        KeyError: 'simple_int'

        >>> config = Environment('APP2', subsection_token='|')
        >>> config.simple_int  # works now because subsections are denoted by |
        '10'
        >>> config.is_typed()
        False
        >>> config.is_writable()
        True
    """

    class Meta:
        is_typed = False

    def __init__(self, prefix, subsection_token='_', **kwargs):
        super(Environment, self).__init__(**kwargs)
        self._prefix = prefix
        self.subsection_token = subsection_token

    def _read(self):
        data = {}
        for keys, value in self._iter_environ():
            keychain = keys.lower().split(self.subsection_token)

            # do not remove prefix when it is an empty string
            # which is only used for accessing system environment
            # variables.
            if self._prefix:
                keychain.pop(0)

            # either the subsection token was changed or the prefix was
            # found in the environment variables without any key name
            # after it. No matter what, in this case we cannot sanely
            # read any data.
            if not keychain:
                continue

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

    def _iter_environ(self):
        prefix_ = self._prefix.lower()
        for key, value in six.iteritems(os.environ):
            if key.lower().startswith(prefix_):
                yield key, value
