# -*- coding: utf-8 -*-

import collections
import re

import six

from .. import converters

__all__ = ['Source']


MetaInfo = collections.namedtuple('MetaInfo', 'readonly is_typed source_name')


class SourceMeta(type):
    """Initialize subclasses and source base class"""

    def __new__(self, name, bases, dct):
        if all([name != 'Source',
                not name.endswith('Mixin'),
                '_read' not in dct]):
            msg = '%s is missing the required "_read" method' % name
            raise NotImplementedError(msg)

        user_meta = dct.get('Meta')

        dct['_meta'] = MetaInfo(
                readonly='_write' not in dct,
                source_name=name,
                is_typed=getattr(user_meta, 'is_typed', True)
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
        self._keychain = kwargs.pop('keychain', ())
        self._parent = kwargs.pop('parent', None)

        # kwargs.get would override the metaclass settings
        # so only change it if it's really given.
        if 'meta' in kwargs:
            self._meta = kwargs.pop('meta')

        # save leftover kwargs to pass them to subsource instances
        # mixins can make use of that to apply attributes to subsources.
        # therefore they should not pop values from kwargs
        self._kwargs = kwargs

    @property
    def _uplink_key(self):
        # the key on the parent that led to this object
        return self._keychain[-1] if self._keychain else None

    # public api
    # ==========
    def get_root(self):
        try:
            return self._parent.get_root()
        except AttributeError:
            return self

    def is_writable(self):
        return not self._meta.readonly

    def is_typed(self):
        return self._meta.is_typed

    def dump(self):
        return self._get_data()

    # dict api
    # ========
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

    def keys(self):
        return sorted(six.iterkeys(self._get_data()))

    def values(self):
        for key in self.keys():
            yield self[key]

    def items(self):
        for key in self.keys():
            yield key, self[key]

    def update(self, *others):
        self._check_writable()

        data = self._get_data()
        for other in others:
            if isinstance(other, Source):
                data.update(other.dump())
            else:
                data.update(other)
        self._set_data(data)

    def __getitem__(self, key):
        attr = self._get_data()[key]
        if isinstance(attr, dict):
            return Source(parent=self,
                          keychain=self._keychain + (key,),
                          meta=self._meta,
                          **self._kwargs
                          )
        return attr

    def __setitem__(self, key, value):
        self._check_writable()

        data = self._get_data()
        data[key] = value
        self._set_data(data)

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

    # internal api
    # ============
    def _get_data(self):
        """Proxies the underlying data source

        Using double underscores should prevent name clashes with
        user defined keys.
        """
        try:
            return self._read()
        except NotImplementedError:
            return self._parent._get_data()[self._uplink_key]

    def _set_data(self, data):
        self._check_writable()

        try:
            self._write(data)
        except NotImplementedError:
            result = self._parent._get_data()
            result[self._uplink_key] = data
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

    def __delattr__(self, name):
        del self[name]

    # required overrides
    # ==================
    def _read(self):


        raise NotImplementedError

    def _write(self, data):


        raise NotImplementedError


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
            # we need to directly call write here otherwise if _set_data
            # raises a NotImplementedError in AbstractSource it will
            # call _get_data which then gets the current cache back
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

    def _set_data(self, data):
        self._check_writable()

        if self._use_cache:
            self._cache = data
        else:
            return super(CacheMixin, self)._set_data(data)


class ConverterMixin(AbstractSource):

    def __init__(self, *args, **kwargs):
        # will be applied to child classes as sublevel sources
        # do not need caching.
        self._converters = [self._make_converter(spec)
                               for spec in kwargs.get('converters', [])]

        super(ConverterMixin, self).__init__(*args, **kwargs)

    def dump(self):
        dumped = super(ConverterMixin, self).dump()

        def convert_dict(data):
            for key, value in data.items():
                typed = self[key]

                if isinstance(typed, Source):
                    yield key, typed.dump()
                else:
                    yield key, typed

        return dict(convert_dict(dumped))

    def _customize(self, key, value):
        converter = self._get_converter(key)
        return converter.customize(value) if converter else value

    def _reset(self, key, value):
        converter = self._get_converter(key)
        return converter.reset(value) if converter else value

    def _make_converter(self, converter_spec):
        if isinstance(converter_spec, converters.Converter):
            return converter_spec
        else:
            return converters.Converter(*converter_spec)

    def _get_converter(self, key):
        search_key = '.'.join(self._keychain + (key,))
        for converter in self._converters:
            if re.search(converter.pattern, search_key):
                return converter

    def __getitem__(self, key):
        attr = super(ConverterMixin, self).__getitem__(key)
        return self._customize(key, attr)

    def __setitem__(self, key, value):
        value = self._reset(key, value)
        super(ConverterMixin, self).__setitem__(key, value)


class DefaultValueMixin(AbstractSource):

    def __init__(self, *args, **kwargs):
        self._add_subsection = kwargs.get('auto_subsection', False)

        super(DefaultValueMixin, self).__init__(*args, **kwargs)

    def __getitem__(self, key):
        try:
            return super(DefaultValueMixin, self).__getitem__(key)
        except KeyError as err:
            if self._add_subsection:
                super(DefaultValueMixin, self).__setattr__(key, {})
                return super(DefaultValueMixin, self).__getitem__(key)
            raise


class Source(CacheMixin,
             DefaultValueMixin,
             ConverterMixin,
             LockedSourceMixin,
             AbstractSource
             ):
    """Source class with all features enabled"""
