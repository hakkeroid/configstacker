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
        """Get the root configuration object from any subsection level.

        Example:
            >>> config = DictSource({'a': {'b': 1}})
            >>> config.a
            DictSource({'b': 1})
            >>> config.a.get_root()
            DictSource({'a': {'b': 1}})
            >>> config is config.a.get_root()
            True
        """
        try:
            return self._parent.get_root()
        except AttributeError:
            return self

    def is_writable(self):
        """Check whether this source loader can be written to."""
        return not self._meta.readonly

    def is_typed(self):
        """Check whether this source loader contains type information.

        This will be used by configstacker to retrieve type information
        for untyped source loaders so that values can be converted
        accordingly.
        """
        return self._meta.is_typed

    def dump(self):
        """Read and dump data from underlying source.

        Returns:
            The dumped data will be a default python :any:`dictionary <dict>`.
        """
        return self._get_data()

    # dict api
    # ========
    def get(self, name, default=None):
        """Same as :any:`dict.get`."""
        try:
            return self[name]
        except KeyError:
            return default

    def setdefault(self, name, value):
        """Same as :any:`dict.setdefault`."""
        try:
            return self[name]
        except KeyError:
            self[name] = value
            return self[name]

    def keys(self):
        """Same as :any:`dict.keys`."""
        return sorted(six.iterkeys(self._get_data()))

    def values(self):
        """Same as :any:`dict.values`."""
        for key in self.keys():
            yield self[key]

    def items(self):
        """Same as :any:`dict.items`."""
        for key in self.keys():
            yield key, self[key]

    def update(self, arg, **kwargs):
        """Same as :any:`dict.update`."""
        self._check_writable()

        data = self._get_data()
        for other in (arg, kwargs):
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
        try:
            return self[name]
        except KeyError:
            return object.__getattribute__(self, name)

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
        """Provide read access to underlying source.

        This method should return the content of the underlying source
        as a simply dictionary. Any recursion needs to be done in this
        method and the returned dictionary must contain the whole
        dataset including subdictionaries. You can make use of
        :any:`utils.make_subdicts` to simplify the recursive part.

        Raises:
            NotImplementedError: Will be raised if this method was not
                overridden in a subclass.
        """
        raise NotImplementedError

    def _write(self, data):
        """Provide write access to underlying source.

        This method is optional and automatically switches the source
        loader into read-only mode if it is not implemented in
        a subclass.

        Args:
            data (dict): Receives a dictionary that needs to be written
                back to the underlying source. Traversing the dictionary
                needs to be done in this method.
        """
        raise NotImplementedError

    # convenience methods
    # ===================
    def _ipython_key_completions_(self):
        # dict-style access tab completion for ipython
        return list(self.keys())


class LockedSourceMixin(AbstractSource):

    def __init__(self, *args, **kwargs):
        self._locked = kwargs.pop('readonly', False)

        super(LockedSourceMixin, self).__init__(*args, **kwargs)

    def is_writable(self):
        """Check whether this source loader can be written to.

        This check depends on the loaders ability to write data back to
        the underlying source and whether the :any:`readonly <Source>`
        parameter was set.
        """
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
        """Write cached data to the underlying source.

        This feature will be active when the :any:`Source's <Source>`
        ``cached=True`` was set initially.

        Raises:
            TypeError: Raised if the source is set to read-only.
        """
        self._check_writable()

        try:
            # we need to directly call write here otherwise if _set_data
            # raises a NotImplementedError in AbstractSource it will
            # call _get_data which then gets the current cache back
            self._write(self._cache)
        except NotImplementedError:
            self._parent.write_cache()

    def clear_cache(self):
        """Empty cache without reloading it.

        The internal cache will be flushed. No other attempt is made to
        reload the data until the value is accessed again. This feature
        will be active when the :any:`Source's <Source>` ``cached=True``
        was set initially.
        """
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
    """Provide a list of prioritized value converters.

    You can either provide :any:`converters <Converter>` or more
    conveniently tuples that can be used to create converters. For that
    to work the first element has to be the key. Then follows the
    customizer function and the third value needs to be the resetter
    function.
    """

    def __init__(self, *args, **kwargs):
        # will be applied to child classes as sublevel sources
        # do not need caching.
        self._converters = [self._make_converter(spec)
                            for spec in kwargs.get('converters', [])]

        super(ConverterMixin, self).__init__(*args, **kwargs)

    def dump(self):
        """Read and dump data from underlying source.

        Additionally all converters will be applied to the returned
        dictionary.

        Returns:
            The dumped data will be a default python :any:`dictionary <dict>`.
        """
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
        except KeyError:
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
    """Base class for all source loaders.

    The source loader handles traversing and accessing the underlying
    data source. Nested sections will be returned as another source
    loader object to ensure that the source loader interface stays the
    same on all levels.

    Args:
        cached (bool): Activate the internal cache to prevent
            immediate writes to the underlying source. Defaults to
            False. You can handle the cache with :any:`clear_cache` and
            :any:`write_cache`

        readonly (bool): Disable the ability to write to this source
            loader. Can be used to open a source without accidentally
            changing it. Defaults to False.

        converters (list): Provide a list of :any:`converters`. Instead
            of converter objects you can also provide simple tuples with
            its elements being the arguments for a converter. That way
            configstacker will create converters on its own.

        auto_subsection (bool): If you are trying to access a value that
            does not exist configstacker usually throws
            a :obj:`KeyError`. Setting this value to True causes
            configstacker to add the missing key as a new subsection
            instead. This defaults to False as

    Raises:
        KeyError: You tried to access a key that does not exist.
        TypeError: You tried to write to a source which is read-only.
    """
