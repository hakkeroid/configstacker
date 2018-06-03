# -*- coding: utf-8 -*-

from collections import deque

from .. import utils
from . import base

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


__all__ = ['INIFile']


class INIFile(base.Source):
    """Source loader for INI-files.

    INI-files are untyped sources. If you need typed data you either
    have to use :any:`configstacker.StackedConfig` with another source
    that is typed or add a :any:`Converter` which takes care of all type
    :ref:`conversions <advanced-converters>`. INI-files are writable by
    default.

    Args:
        source (str): A path to an INI-file.

        subsection_token (str, optional): Will be used to split
            a section header into subsections. Defaults to ``.``.

        root_section (str, optional): Will be used to identify the root
            section in the INI file. Defaults to `__root__`.

        kwargs: See :any:`Source` for additional options.

    Examples:
        >>> from configstacker import INIFile
        >>> config = INIFile('path/to/config.ini')
        >>> config.simple_int
        '10'
        >>> config.is_typed()
        False
        >>> config.is_writable()
        True
    """

    class Meta:
        is_typed = False

    def __init__(self, source, subsection_token=None, root_section='__root__',
                 **kwargs):
        super(INIFile, self).__init__(**kwargs)
        self._source = source
        self.subsection_token = subsection_token
        self.root_section = root_section
        self._parser = _parse_source(source)

    def _read(self):
        data = {}
        for section in self._parser.sections():
            if section == self.root_section:
                subsections = []
            elif self.subsection_token and self.subsection_token in section:
                subsections = section.split(self.subsection_token)
            else:
                subsections = [section]

            items = self._parser.items(section)
            subdict = utils.make_subdicts(data, subsections)
            subdict.update(items)

        return data

    def _write(self, data):
        data_ = {}

        sections = deque([(None, data.items())])

        while sections:
            section, items = sections.popleft()

            if not items:
                data_[section] = items
                continue

            for key, value in items:
                if isinstance(value, dict):
                    if section is None:
                        name = key
                    else:
                        name = self.subsection_token.join([section, key])
                    sections.append((name, value.items()))
                else:
                    data_.setdefault(section or '__root__', []).append((key, value))

        existing_sections = self._parser.sections()

        for section, items in data_.items():
            if section not in existing_sections:
                self._parser.add_section(section)
            for key, value in items:
                self._parser.set(section, key, str(value))

        with open(self._source, 'w') as fh:
            self._parser.write(fh)


def _parse_source(source):
    parser = configparser.ConfigParser()

    try:
        with open(source) as fh:
            parser._read(fh, fh.name)
    except TypeError:
        parser._read(source, source)

    return parser
