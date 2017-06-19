# -*- coding: utf-8 -*-

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from . import base


class INIFile(base.Source):
    """Source for ini files"""

    _is_typed = False

    def __init__(self, source, subsection_token=None, **kwargs):
        super(INIFile, self).__init__(**kwargs)
        self._source = source
        self._token = subsection_token
        self._parser = _parse_source(source)

    def _read(self):
        data = {}
        for section in self._parser.sections():
            if section == '__root__':
                subsections = []
            elif self._token and self._token in section:
                subsections = section.split(self._token)
            else:
                subsections = [section]

            items = self._parser.items(section)
            subdict = _make_subdicts(data, subsections)
            subdict.update(items)

        return data


def _make_subdicts(base, subkeys):
    while subkeys:
        subsection = subkeys.pop(0)
        base = base.setdefault(subsection, {})
    return base


def _parse_source(source):
    parser = configparser.ConfigParser()

    try:
        with open(source) as fh:
            parser._read(fh, fh.name)
    except TypeError:
        parser._read(source, source)

    return parser
