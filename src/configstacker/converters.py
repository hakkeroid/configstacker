# -*- coding: utf-8 -*-

import collections
import datetime
import distutils
import fnmatch
import re

import six

__all__ = ['bools', 'dates', 'datetimes']


class Converter(collections.namedtuple('_', 'key customize reset')):
    def __new__(cls, key, customize, reset):
        return super(Converter, cls).__new__(cls, key, customize, reset)

    @property
    def pattern(self):
        return fnmatch.translate(self.key)

    def __repr__(self):
        return "Converter(key='{self.key}', " \
               "customize='{self.customize.__name__}', " \
               "reset='{self.reset.__name__}')".format(self=self)


def bools(key):
    def to_bool(value):
        return bool(distutils.util.strtobool(value))

    return Converter(key, to_bool, str)


def dates(key, fmt='%Y-%m-%d'):
    def to_obj(date_str):
        return datetime.datetime.strptime(date_str, fmt).date()

    def to_str(date_obj):
        return date_obj.strftime(fmt)

    return Converter(key, to_obj, to_str)


def datetimes(key, fmt='%Y-%m-%dT%H:%M:%S'):
    def to_obj(date_str):
        return datetime.datetime.strptime(date_str, fmt)

    def to_str(datetime_obj):
        return datetime_obj.strftime(fmt)

    return Converter(key, to_obj, to_str)
