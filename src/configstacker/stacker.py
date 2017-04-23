# -*- coding: utf-8 -*-

from collections import defaultdict, deque

from . import types
from .sources import DictSource, Source

try:
    from collections.abc import MutableSequence
except ImportError:
    from collections import MutableSequence


class SourceIterator(MutableSequence):

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

    def insert(self, pos, item):
        self._validate_sources([item])
        self._sources.insert(pos, item)

    def typed(self):
        def filter_by_type(source):
            return source.is_typed()

        for source in self._iter_sources(filter_by_type):
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
            if not isinstance(source, Source):
                msg = "A source must be a subclass of 'configstacker.sources.Source' not '%s'"
                raise ValueError(msg % source.__class__.__name__)

    def __len__(self):
        return len(self._sources)

    def __getitem__(self, index):
        return self._sources[index]

    def __setitem__(self, index, value):
        self._validate_sources([value])
        self._sources[index] = value

    def __delitem__(self, item):
        del self._sources[item]

    def __iter__(self):
        return self._iter_sources()

    def __repr__(self):
        return 'SourceIterator(%s)' % repr(self._sources)


class StackedConfig(object):
    """Multi layer config object"""

    # disable setattr as long as we initialize instance attributes
    _initialized = False

    def __init__(self, *sources, **kwargs):
        if not sources:
            sources = [DictSource()]

        # _keychain is a list of keys that led from the root
        # config to this (sub)config
        self._keychain = kwargs.pop('keychain', [])

        self.source_list = SourceIterator(
            *sources,
            keychain=self._keychain,
            reverse=kwargs.pop('reverse', True)
        )

        # custom strategies that describes how to merge multiple
        # values of the same key
        self._strategy_map = kwargs.pop('strategies', {})

        # inform user about unknown parameters
        if kwargs:
            raise TypeError('unknown parameters specified %s' % kwargs)

        # activate setattr
        self._initialized = True

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def items(self):
        def _items():
            subqueues = defaultdict(deque)

            yielded = set()
            results = {}

            for source in self.source_list:
                for key, value in source.items():
                    # identical keys from different sources that have
                    # dicts as values needs to be merged
                    if isinstance(value, dict):
                        # higher prio sources might override keys with
                        # simple values that otherwise point to subsections
                        if key in yielded:
                            msg = ("The key '%s' from '%s' specifies a"
                                   " subsection as value which conflicts"
                                   " with a higher prioritized source"
                                   " that wants the same value to be a"
                                   " non-sectional instead")
                            raise ValueError(msg % (key, source._meta.source_name))
                        subqueues[key].appendleft(source.get_root())
                        continue

                    if key in subqueues:
                        msg = ("The key '%s' from '%s' specifies a"
                               " non-sectional value which conflicts"
                               " with a higher prioritized source"
                               " that wants the same value to be a"
                               " subsection instead.")
                        raise ValueError(msg % (key, source._meta.source_name))

                    if not source.is_typed():
                        value = self._get_typed_value(key, value)

                    # all other identical keys will shadow
                    # subsequent keys
                    if key in self._strategy_map:
                        strategy = self._strategy_map[key]
                        results[key] = strategy(results.get(key), value)
                    elif key in yielded:
                        continue
                    else:
                        yield key, value
                        yielded.add(key)

            for key, value in results.items():
                yield key, value

            for key, subqueue in subqueues.items():
                yield key, self._make_subconfig(subqueue, key)

        return sorted(_items())

    def setdefault(self, name, value):
        try:
            return self[name]
        except KeyError:
            self[name] = value
            return value

    def update(self, *others):
        for other in others:
            for key, value in other.items():
                self[key] = value

    def dump(self):
        def _dump(obj):
            for key, value in obj.items():
                if isinstance(value, StackedConfig):
                    yield key, dict(_dump(value))
                else:
                    yield key, value

        return dict(_dump(self))

    def _get_typed_value(self, key, value):
        for source in self.source_list.typed():
            try:
                typed_value = source[key]
            except KeyError:
                continue

            type_info = types.get_type_info(typed_value)
            return types.convert_value_to_type(value, type_info)
        return value

    def _make_subconfig(self, sources, key):
        return StackedConfig(*sources,
                             keychain=self._keychain+[key],
                             strategies=self._strategy_map
                             )

    def __getattr__(self, key):
        return self[key]

    def __getitem__(self, key):
        # will be used as input for a new sublevel config with the
        # key added to the keychain.
        subqueue = deque()

        strategy = self._strategy_map.get(key)
        result = None

        for source in self.source_list:
            try:
                value = source[key]
            except KeyError:
                continue

            if isinstance(value, Source):
                subqueue.appendleft(source.get_root())
                continue

            if not source.is_typed():
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
        # will be used if the key could not be found in any source
        # which means that a new key/value shall be added to the
        # config.
        writable_source = None

        for source in self.source_list:
            if writable_source is None and source.is_writable():
                writable_source = source

            if key in source:
                source[key] = value
                return

        # no source was found so write it to first writable source
        if writable_source is not None:
            writable_source[key] = value
        else:
            raise TypeError('No writable sources found')

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
