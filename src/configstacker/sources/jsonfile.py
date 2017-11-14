# -*- coding: utf-8 -*-

import json

from . import base

__all__ = ['JSONFile']


class JSONFile(base.Source):
    """Source loader for json files.

    Json files are typed sources and by default writable.

    Args:
        source (str): A path to a json file.

        kwargs: See :any:`Source` for additional options.

    Examples:
        >>> from configstacker import JSONFile
        >>> config = JSONFile('path/to/config.json')
        >>> config.simple_int
        10
        >>> config.is_typed()
        True
        >>> config.is_writable()
        True
    """

    def __init__(self, source, **kwargs):
        super(JSONFile, self).__init__(**kwargs)
        self._source = source

    def _read(self):
        with open(self._source) as fh:
            return json.load(fh)

    def _write(self, data):
        with open(self._source, 'w') as fh:
            json.dump(data, fh)
