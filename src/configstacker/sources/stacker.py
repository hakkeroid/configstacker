# -*- coding: utf-8 -*-

import distutils

from collections import defaultdict, deque

from .. import converters, strategies
from . import base, dictsource

try:
    from collections.abc import MutableSequence
except ImportError:
    from collections import MutableSequence

__all__ = ['StackedConfig']


class SourceList(MutableSequence):

    def __init__(self, *sources, **kwargs):
        self._validate_sources(sources)
        self._sources = list(sources)

        # _keychain is a list of keys that leads from the root
        # config to the subconfig
        self.keychain = kwargs.pop('keychain', [])

        # convenience functionality that allows to specify
        # the priority for traversing the sources
        self.reverse = kwargs.pop('reverse', None)

        if kwargs:
            raise ValueError('Unknown parameters: %s' % kwargs)

    def _check_mutability(self):
        if self.keychain:
            raise TypeError("The source list of a sublevel configuration"
                            " cannot be mutated")

    def insert(self, pos, item):
        self._check_mutability()
        self._validate_sources([item])
        self._sources.insert(pos, item)

    def typed(self):
        def filter_by_type(source):
            return source.is_typed()

        for source in self._iter_sources(filter_by_type):
            yield source

    def writable(self):
        def filter_by_writability(source):
            return source.is_writable()

        for source in self._iter_sources(filter_by_writability):
            yield source

    def _iter_sources(self, filter_fn=None):
        if not filter_fn:
            def filter_fn(s):
                return True

        order = reversed if self.reverse else lambda x: x

        # return the sublevels of the sources according to the
        # keychain
        for source in order(self._sources):
            if filter_fn(source) is False:
                continue
            traversed_source = source
            for key in self.keychain:
                traversed_source = traversed_source[key]
            yield traversed_source

    def _validate_sources(self, sources):
        for source in sources:
            if not isinstance(source, base.Source):
                msg = ("A source must be a subclass of"
                       " 'configstacker.sources.Source' not '%s'")
                raise ValueError(msg % source.__class__.__name__)

    def __len__(self):
        return len(self._sources)

    def __getitem__(self, index):
        return self._sources[index]

    def __setitem__(self, index, value):
        self._check_mutability()
        self._validate_sources([value])
        self._sources[index] = value

    def __delitem__(self, item):
        del self._sources[item]

    def __iter__(self):
        return self._iter_sources()

    def __repr__(self):
        return 'SourceList(%s)' % repr(self._sources)


class StackedConfig(object):
    """Multi layer config object"""

    # disable setattr as long as we initialize instance attributes
    _initialized = False

    def __init__(self, *sources, **kwargs):
        if not sources:
            sources = [dictsource.DictSource()]

        # _parent is the parent object
        # _parent_key is the key on the parent that led to this object
        self._parent, self._parent_key = kwargs.pop('parent', (None, None))

        # _keychain is a list of keys that led from the root
        # config to this (sub)config
        self._keychain = kwargs.pop('keychain', [])

        # exposing the source list through an attribute and manipulating
        # it directly contradicts with the law of demeter. However, in
        # this case implementing the source list's interface would make
        # the stacker's interface unneccessarily complex and adds more
        # keywords that has to be escaped through dict access.
        # https://en.wikipedia.org/wiki/Law_of_Demeter.
        self.source_list = SourceList(
            *sources,
            keychain=self._keychain,
            reverse=kwargs.pop('reverse', True)
        )

        # custom strategies that describe how to merge multiple
        # values of the same key
        self._strategy_map = kwargs.pop('strategy_map', {})
        # custom converters that define how to deal with individual
        # values
        self._converter_map = converters.make_converter_map(
            kwargs.pop('converter_map', {})
        )

        # inform user about unknown parameters
        if kwargs:
            raise TypeError('unknown parameters specified %s' % kwargs)

        # activate setattr
        self._initialized = True

    def get_root(self):
        try:
            return self._parent.get_root()
        except AttributeError:
            return self

    def is_writable(self):
        try:
            next(self.source_list.writable())
        except StopIteration:
            return False
        else:
            return True

    def is_typed(self):
        try:
            next(self.source_list.typed())
        except StopIteration:
            return False
        else:
            return True

    def dump(self):
        def _dump(obj):
            for key, value in obj.items():
                if isinstance(value, StackedConfig):
                    yield key, dict(_dump(value))
                else:
                    yield key, value

        return dict(_dump(self))

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
            return value

    def keys(self):
        def key_iterator():
            yielded_keys = set()

            for source in self.source_list:
                for key in source:
                    if key not in yielded_keys:
                        yield key
                        yielded_keys.add(key)

        return sorted(key_iterator())

    def values(self):
        for key in self.keys():
            yield self[key]

    def items(self):
        for key in self.keys():
            yield key, self[key]

    def update(self, *others):
        for other in others:
            for key, value in other.items():
                self[key] = value

    def _get_typed_value(self, key, value):
        for source in self.source_list.typed():
            try:
                typed_value = source[key]
            except KeyError:
                continue

            type_info = type(typed_value)
            return _convert_value_to_type(value, type_info)
        return value

    def _make_subconfig(self, sources, key):
        return StackedConfig(*sources,
                             parent=(self, key),
                             keychain=self._keychain+[key],
                             strategy_map=self._strategy_map,
                             converter_map=self._converter_map
                             )

    def __getattr__(self, key):
        return self[key]

    def __getitem__(self, key):
        # will be used as input for a new sublevel config with the
        # key added to the keychain.
        subqueue = deque()

        strategy = self._strategy_map.get(key)
        converter = self._converter_map.get(key)
        result = strategies.EMPTY

        for source in self.source_list:
            try:
                value = source[key]
            except KeyError:
                continue

            if converter:
                if not source.is_typed():
                    value = self._get_typed_value(key, value)

                value = converter.customize(value)

            if isinstance(value, base.Source):
                subqueue.appendleft(source.get_root())
                continue

            if not converter and not source.is_typed():
                value = self._get_typed_value(key, value)

            if strategy:
                result = strategy(result, value)
            else:
                return value

        # in the while loop we always ended up in any of the continue
        # statements which means either the key was not found or the key
        # is a sublevel source or it is untyped.
        if strategy:
            return result
        elif subqueue:
            return self._make_subconfig(subqueue, key)
        else:
            raise KeyError("Key '%s' was not found" % key)

    def __setattr__(self, attr, value):
        if any([self._initialized is False,
                attr == '_initialized',
                attr in self.__dict__,
                attr in StackedConfig.__dict__]):
            super(StackedConfig, self).__setattr__(attr, value)
        else:
            self[attr] = value

    def __setitem__(self, key, value):
        for source in self.source_list:
            if key in source:
                source[key] = value
                return

        # no source was found so write it to first writable source
        try:
            writable_source = next(self.source_list.writable())
        except StopIteration:
            raise TypeError('No writable sources found')
        else:
            writable_source[key] = value

    def __eq__(self, other):
        return self.dump() == other.dump()

    def __len__(self):
        return len(list(iter(self)))

    def __iter__(self):
        yielded = set()

        for source in self.source_list:
            for key in source:
                if key in yielded:
                    continue

                yielded.add(key)
                yield key

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, repr(self.dump()))


def _convert_value_to_type(value, type_info):
    """Convert value by dispatching from type_info"""

    if type_info is list:
        return [token.strip() for token in value.split(',')]

    elif type_info is tuple:
        return tuple(token.strip() for token in value.split(','))

    elif type_info is set:
        return set([token.strip() for token in value.split(',')])

    elif type_info is bool:
        try:
            return bool(distutils.util.strtobool(value))
        except ValueError:
            return value
    else:
        return type_info(value)


