# -*- coding: utf-8 -*-

from collections import deque
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from . import base
from .. import utils

__all__ = ['INIFile']


class INIFile(base.Source):
    """Source for ini files"""

    class Meta:
        is_typed = False

    def __init__(self, source, subsection_token=None, **kwargs):
        super(INIFile, self).__init__(**kwargs)
        self._source = source
        self.subsection_token = subsection_token
        self._parser = _parse_source(source)

    def _read(self):
        data = {}
        for section in self._parser.sections():
            if section == '__root__':
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
