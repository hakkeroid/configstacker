# -*- coding: utf-8 -*-

import collections

import six

from .. import typing

__all__ = ['Source']


MetaInfo = collections.namedtuple('MetaInfo', 'readonly is_typed source_name')


class SourceMeta(type):
    """Initialize subclasses and source base class"""

    def __new__(self, name, bases, dct):
        if all([not '_read' in dct,
                name != 'Source',
                not name.endswith('Mixin')]):
            msg = '%s is missing the required "_read" method' % name
            raise NotImplementedError(msg)

        dct['_meta'] = MetaInfo(
                readonly='_write' not in dct,
                source_name=name,
                is_typed=dct.get('_is_typed', True)
        )

        return super(SourceMeta, self).__new__(self, name, bases, dct)

    def __call__(cls, *args, **kwargs):
        instance = super(SourceMeta, cls).__call__(*args, **kwargs)
        instance._initialized = True
        return instance


@six.add_metaclass(SourceMeta)
class AbstractSource(object):
    """A source tree container

    The AbstractSource handles traversing and accessing
    the underlying data map. Nested values will be returned
    as another source object which keeps a reverse link
    to the parent source.
    """

    _initialized = False

    def __init__(self, **kwargs):
        # _parent is the parent object
        # _parent_key is the key on the parent that led to this object
        self._parent, self._parent_key = kwargs.pop('parent', (None, None))

        # kwargs.get would override the metaclass settings
        # so only change it if it's really given.
        if 'meta' in kwargs:
            self._meta = kwargs.pop('meta')

        # save leftover kwargs to pass them to subsource instances
        # mixins can make use of that to apply attributes to subsources.
        # therefore they should not pop values from kwargs
        self._kwargs = kwargs

    def get_root(self):
        try:
            return self._parent.get_root()
        except AttributeError:
            return self

    def is_writable(self):
        return not self._meta.readonly

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def setdefault(self, name, value):
        try:
            return self[name]
        except KeyError:
            self[name] = value
            return self[name]

    def items(self):
        return sorted(six.iteritems(self._get_data()))

    def values(self):
        return sorted(six.iterkeys(self._get_data()))

    def keys(self):
        return sorted(six.iterkeys(self._get_data()))

    def update(self, *others):
        self._check_writable()

        data = self._get_data()
        for other in others:
            if isinstance(other, Source):
                data.update(other.dump())
            else:
                data.update(other)
        self._set_data(data)

    def dump(self):
        return self._get_data()

    def is_typed(self):
        return self._meta.is_typed

    def _read(self):
        raise NotImplementedError

    def _write(self, data):
        raise NotImplementedError

    def _get_data(self):
        """Proxies the underlying data source

        Using double underscores should prevent name clashes with
        user defined keys.
        """
        try:
            return self._read()
        except NotImplementedError:
            return self._parent._get_data()[self._parent_key]

    def _set_data(self, data):
        self._check_writable()

        try:
            self._write(data)
        except NotImplementedError:
            result = self._parent._get_data()
            result[self._parent_key] = data
            self._parent._set_data(result)

    def _check_writable(self):
        if self._meta.readonly:
            raise TypeError('%s is a read-only source' % self._meta.source_name)

    def __getattr__(self, name):
        # although the key was accessed with attribute style
        # lets keep raising a KeyError to distinguish between
        # internal and user data.
        return self[name]

    def __setattr__(self, attr, value):
        if any([self._initialized is False,
                attr == '_initialized',
                attr in self.__dict__,
                attr in self.__class__.__dict__]):
            super(AbstractSource, self).__setattr__(attr, value)
        else:
            self[attr] = value

    def __getitem__(self, key):
        attr = self._get_data()[key]
        if isinstance(attr, dict):
            return Source(parent=(self, key),
                          meta=self._meta,
                          **self._kwargs
                          )
        return attr

    def __setitem__(self, key, value):
        self._check_writable()

        data = self._get_data()
        data[key] = value
        self._set_data(data)

    def __delattr__(self, name):
        del self[name]

    def __delitem__(self, key):
        self._check_writable()

        data = self._get_data()
        del data[key]
        self._set_data(data)

    def __len__(self):
        return len(self._get_data().keys())

    def __iter__(self):
        return iter(self._get_data().keys())

    def __eq__(self, other):
        return self._get_data() == other

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, repr(self._get_data()))


class LockedSourceMixin(AbstractSource):

    def __init__(self, *args, **kwargs):
        self._locked = kwargs.pop('readonly', False)

        super(LockedSourceMixin, self).__init__(*args, **kwargs)

    def is_writable(self):
        is_writable = super(LockedSourceMixin, self).is_writable()
        return is_writable and not self._locked

    def _check_writable(self):
        super(LockedSourceMixin, self)._check_writable()

        if self._locked:
            raise TypeError('%s is locked and cannot be changed' % self._meta.source_name)


class CacheMixin(AbstractSource):

    def __init__(self, *args, **kwargs):
        # will be applied to top level source classes only as nested
        # sublevels which are also Source instances do not need caching.
        self._use_cache = kwargs.pop('cached', False)
        self._cache = None

        super(CacheMixin, self).__init__(*args, **kwargs)

    def write_cache(self):
        self._check_writable()

        try:
            self._write(self._cache)
        except NotImplementedError:
            self._parent.write_cache()

    def clear_cache(self):
        self._cache = None

    def _get_data(self):
        if self._use_cache and self._cache:
            return self._cache

        self._cache = super(CacheMixin, self)._get_data()
        return self._cache

        return super(CacheMixin, self)._get_data()

    def _set_data(self, data):
        self._check_writable()

        if self._use_cache:
            self._cache = data
        else:
            return super(CacheMixin, self)._set_data(data)


class CustomTypeMixin(AbstractSource):

    def __init__(self, *args, **kwargs):
        # will be applied to child classes as sublevel sources
        # do not need caching.
        self._custom_types = typing.make_type_map(kwargs.get('type_map', {}))

        super(CustomTypeMixin, self).__init__(*args, **kwargs)

    def dump(self, typed=False):
        dumped = super(CustomTypeMixin, self).dump()

        if typed is False:
            return dumped

        def convert_dict(data):
            for key, value in data.items():
                if isinstance(value, dict):
                    yield key, dict(convert_dict(value))
                else:
                    yield key, self._to_custom_type(key, value)

        return dict(convert_dict(dumped))

    def _to_custom_type(self, key, value):
        converter = self._custom_types.get(key)
        return converter.customize(value) if converter else value

    def _to_original_type(self, key, value):
        converter = self._custom_types[key]
        return converter.reset(value) if converter else value

    def __getitem__(self, key):
        attr = super(CustomTypeMixin, self).__getitem__(key)
        if isinstance(attr, Source):
            return attr

        return self._to_custom_type(key, attr)

    def __setitem__(self, key, value):
        if key in self._custom_types:
            value = self._to_original_type(key, value)
        super(CustomTypeMixin, self).__setitem__(key, value)


class DefaultValueMixin(AbstractSource):

    def __init__(self, *args, **kwargs):
        self._default_value = kwargs.get('default_for_missing', None)

        super(DefaultValueMixin, self).__init__(*args, **kwargs)

    def __getitem__(self, key):
        try:
            return super(DefaultValueMixin, self).__getitem__(key)
        except KeyError as err:
            if self._default_value is not None:
                super(DefaultValueMixin, self).__setattr__(
                        key, self._default_value)
                return super(DefaultValueMixin, self).__getitem__(key)
            raise


class Source(CacheMixin,
             DefaultValueMixin,
             CustomTypeMixin,
             LockedSourceMixin,
             AbstractSource
             ):
    """Source class with all features enabled"""
