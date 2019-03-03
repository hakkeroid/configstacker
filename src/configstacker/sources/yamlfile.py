# -*- coding: utf-8 -*-

try:
    import yaml
except ImportError:
    pass

from . import base

__all__ = ['YAMLFile']


class YAMLFile(base.Source):
    """Source loader for yaml files.

    Yaml files are typed sources and by default writable.

    Args:
        source (str): A path to a yaml file.

        kwargs: See :any:`Source` for additional options.

    Examples:
        >>> from configstacker import YAMLFile
        >>> config = YAMLFile('path/to/config.yml')
        >>> config.simple_int
        10
        >>> config.is_typed()
        True
        >>> config.is_writable()
        True
    """

    def __init__(self, source, **kwargs):
        try:
            assert yaml
        except NameError:
            raise ImportError('You are missing the optional'
                              ' dependency "pyyaml"')

        super(YAMLFile, self).__init__(**kwargs)
        self._source = source

    def _read(self):
        with open(self._source) as fh:
            return yaml.safe_load(fh)

    def _write(self, data):
        with open(self._source, 'w') as fh:
            yaml.dump(data, fh)
