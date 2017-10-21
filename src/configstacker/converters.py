# -*- coding: utf-8 -*-

from collections import namedtuple
import datetime
import distutils

import six

__all__ = ['bools', 'dates', 'datetimes']


Converter = namedtuple('Converter', 'key customize reset')

def bools():
    def to_bool(value):
        return bool(distutils.util.strtobool(value))

    return (to_bool, str)


def dates(fmt='%Y-%m-%d'):
    def to_obj(date_str):
        return datetime.datetime.strptime(date_str, fmt).date()

    def to_str(date_obj):
        return date_obj.strftime(fmt)

    return (to_obj, to_str)


def datetimes(fmt='%Y-%m-%dT%H:%M:%S'):
    def to_obj(date_str):
        return datetime.datetime.strptime(date_str, fmt)

    def to_str(datetime_obj):
        return datetime_obj.strftime(fmt)

    return (to_obj, to_str)


def make_converter_map(mapping):
    def create_converter(mapping):
        for key, values in six.iteritems(mapping):
            try:
                yield key, Converter(key, *values)
            except TypeError:
                # Is already a Converter.
                yield key, values

    return dict(create_converter(mapping))
