# -*- coding: utf-8 -*-

from collections import namedtuple

import six

__all__ = ['Converter', 'make_converter_map']


Converter = namedtuple('Converter', 'key customize reset')


def make_converter_map(mapping):
    def create_converter(mapping):
        for key, values in six.iteritems(mapping):
            try:
                yield key, Converter(key, *values)
            except TypeError:
                # Is already a Converter.
                yield key, values

    return dict(create_converter(mapping))
