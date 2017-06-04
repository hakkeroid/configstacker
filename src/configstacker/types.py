# -*- coding: utf-8 -*-

from collections import namedtuple

CustomType = namedtuple('CustomType', 'customize reset')


def get_type_info(value):
    return type(value)


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
