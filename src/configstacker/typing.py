# -*- coding: utf-8 -*-

from collections import namedtuple

import six

__all__ = ['CustomType', 'convert_value_to_type']


CustomType = namedtuple('CustomType', 'key customize reset')


def convert_value_to_type(value, type_info):
    """Convert value by dispatching from type_info"""

    if type_info is list:
        return [token.strip() for token in value.split(',')]

    elif type_info is tuple:
        return tuple(token.strip() for token in value.split(','))

    elif type_info is set:
        return set([token.strip() for token in value.split(',')])

    elif type_info is bool:
        if value.lower() == 'false':
            return False
        elif value.lower() == 'true':
            return True
        else:
            return value
    else:
        return type_info(value)


def make_type_map(mapping):
    def convert_to_type(mapping):
        for key, values in six.iteritems(mapping):
            try:
                yield key, CustomType(key, *values)
            except TypeError:
                # Is already a CustomType.
                yield key, values

    return dict(convert_to_type(mapping))
