# -*- coding: utf-8 -*-

import collections
import datetime
import distutils
import fnmatch

__all__ = ['Converter', 'bools', 'dates', 'datetimes']


class Converter(collections.namedtuple('_', 'key customize reset')):
    """Convert configuration values based on their name.

    The converter will be used by configstacker in the read and write
    process to change values as defined by its customize and reset
    methods.

    The customize and reset functions will be called with a single value
    and they are required to also return a single value. Other than that
    the methods can be any callable and you can make use of your own
    functions or the :py:mod:`builtin converters <configstacker.converters>`.

    Args:
        key (str): The name of the configuration key that shall be modified.
        customize (:obj:`function`): The desired :any:`customize` function
            or callable as described below.
        reset (:obj:`function`): The desired :any:`reset` function or
            callable as described below.

    .. py:function:: customize(value)

        This function will be called by configstacker in the read
        process to convert the raw configuration value into the desired
        value.

        :param value:
            This is the raw value as read from the source loader.

        :return:
            The method should return the desired value.

    .. py:function:: reset(value)

        This function will be called by configstacker in the write
        process to revert the previously converted value back to a raw
        presentation.

        :param value:
            This is the value how it was returned by the customize
            method.

        :return:
            The method should return a value that will be understood by
            the underlying source handler.
    """
    def __new__(cls, key, customize, reset):
        return super(Converter, cls).__new__(cls, key, customize, reset)

    @property
    def pattern(self):
        """The regex pattern as derived from the specified key"""
        return fnmatch.translate(self.key)

    def __repr__(self):
        return "Converter(key='{self.key}', " \
               "customize='{self.customize.__name__}', " \
               "reset='{self.reset.__name__}')".format(self=self)


def bools(key):
    """Convert between strings and bools

    Args:
        key (str): The name of the configuration key that shall be modified.

    Returns:
        A converter object that turns strings into True and False or
        booleans to strings.
    """
    @_copy_docs(distutils.util.strtobool)
    def to_bool(value):
        return bool(distutils.util.strtobool(value))

    return Converter(key, to_bool, str)


def dates(key, fmt='%Y-%m-%d'):
    """Convert between strings and dates

    Args:
        key (str): The name of the configuration key that shall be modified.
        fmt (str): The `strptime and strftime format`_

    Returns:
        A converter object that turns strings into :any:`datetime.date`
        objects.

    .. _strptime and strftime format: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
    """  # noqa: E501
    @_copy_docs(datetime.datetime.strptime)
    def to_obj(date_str):
        return datetime.datetime.strptime(date_str, fmt).date()

    @_copy_docs(datetime.datetime.strftime)
    def to_str(date_obj):
        return date_obj.strftime(fmt)

    return Converter(key, to_obj, to_str)


def datetimes(key, fmt='%Y-%m-%dT%H:%M:%S'):
    """Convert between strings and datetimes

    Args:
        key (str): The name of the configuration key that shall be modified.
        fmt (str): The `strptime and strftime format`_

    Returns:
        A converter object that turns strings into :any:`datetime.datetime`
        objects.

    .. _strptime and strftime format: https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
    """  # noqa: E501
    @_copy_docs(datetime.datetime.strptime)
    def to_obj(date_str):
        return datetime.datetime.strptime(date_str, fmt)

    @_copy_docs(datetime.datetime.strftime)
    def to_str(datetime_obj):
        return datetime_obj.strftime(fmt)

    return Converter(key, to_obj, to_str)


def _copy_docs(from_fn):
    def wrapper(to_fn):
        to_fn.__doc__ = from_fn.__doc__
        return to_fn
    return wrapper
