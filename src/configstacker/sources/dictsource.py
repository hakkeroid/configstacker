# -*- coding: utf-8 -*-

import copy

from . import base

__all__ = ['DictSource']


class DictSource(base.Source):
    """Simple in-memory key-value source.

    Because this source loader is based on a python dictionary it is
    inherintly typed and writable. However, it is seldom useful on its
    own except for testing purposes. It makes a great addition to
    a stacked configuration though. There it can serve as

        - a source for default values.
        - a source for type information when otherwise there are only
          untyped sources in use.
        - a great way to provide a source where changes can be written
          to, in case all other sources are write protected.

    Args:
        data (dict): A dictionary of data that serves as the source.

        kwargs: See :any:`Source` for additional options.

    Examples:
        >>> from configstacker import DictSource
        >>> config = DictSource({'simple_int': 10})
        >>> config.simple_int
        10
        >>> config.is_typed()
        True
        >>> config.is_writable()
        True
    """

    def __init__(self, data=None, **kwargs):
        super(DictSource, self).__init__(**kwargs)
        self._data = data or {}

    def _read(self):
        # use deepcopy to prevent uncontrolled changes
        # to self._data from outside of this class
        return copy.deepcopy(self._data)

    def _write(self, data):
        self._data = data
