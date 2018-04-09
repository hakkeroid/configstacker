# -*- coding: utf-8 -*-

import distutils
import re
import sys

from collections import defaultdict, deque

import six

from .. import converters, strategies
from . import base, dictsource

try:
    from collections.abc import MutableSequence
except ImportError:
    from collections import MutableSequence

__all__ = ['StackedConfig']

PY35 = sys.version_info[0:2] >= (3, 5)


class SourceList(MutableSequence):

    def __init__(self, *sources, **kwargs):
        self._validate_sources(sources)
        self._sources = list(sources)

        # _keychain is a list of keys that leads from the root
        # config to the subconfig
        self._keychain = kwargs.pop('keychain', ())

        # convenience functionality that allows to specify
        # the priority for traversing the sources
        if kwargs.pop('reverse', False):
            self.reverse()

        if kwargs:
            raise ValueError('Unknown parameters: %s' % kwargs)

    def _check_mutability(self):
        if self._keychain:
            raise TypeError("The source list of a sublevel configuration"
                            " cannot be mutated")

    def insert(self, index, source):
        self._check_mutability()
        self._validate_sources([source])
        self._sources.insert(index, source)

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

        # return the sublevels of the sources according to the
        # keychain
        for source in reversed(self._sources):
            if filter_fn(source) is False:
                continue
            traversed_source = source
            for key in self._keychain:
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
        if not PY35:
            item -= 1
        del self._sources[item]

    def __iter__(self):
        return self._iter_sources()

    def __repr__(self):
        return 'SourceList(%s)' % repr(self._sources)


class StackedConfig(base.Source):
    """Multi layer config object"""


    def __init__(self, *sources, **kwargs):
        super(StackedConfig, self).__init__(**kwargs)

        if not sources:
            sources = [dictsource.DictSource()]

        # exposing the source list through an attribute and manipulating
        # it directly contradicts with the law of demeter. However, in
        # this case implementing the source list's interface would make
        # the stacker's interface unneccessarily complex and adds more
        # keywords that has to be escaped through dict access.
        # https://en.wikipedia.org/wiki/Law_of_Demeter.
        self.source_list = SourceList(
            *sources,
            keychain=self._keychain,
            reverse=kwargs.pop('reverse', False)
        )

        # custom strategies that describe how to merge multiple
        # values of the same key
        self.strategy_map = kwargs.pop('strategy_map', {})

    # public api
    # ==========
    def is_writable(self):
        for source in self.source_list.writable():
            return True
        return False

    def is_typed(self):
        for source in self.source_list.typed():
            return True
        return False

    def dump(self):
        def _dump(obj):
            for key, value in obj.items():
                if isinstance(value, StackedConfig):
                    yield key, dict(_dump(value))
                else:
                    yield key, value

        return dict(_dump(self))

    # dict api
    # ========
    def keys(self):
        def key_iterator():
            yielded_keys = set()

            for source in self.source_list:
                for key in source:
                    if key not in yielded_keys:
                        yield key
                        yielded_keys.add(key)

        return sorted(key_iterator())

    def update(self, *others):
        for other in others:
            for key, value in other.items():
                self[key] = value

    def __getitem__(self, key):
        # will be used as input for a new sublevel config with the
        # key added to the keychain.
        subsections = deque()

        converter = self._get_converter(key)

        strategy = self.strategy_map.get(key)
        result = strategies.EMPTY

        for source in self.source_list:
            try:
                value = source[key]
            except KeyError:
                # continue until we found the key in one of the sources.
                continue

            # the key was found and holds a subsection, so either..
            if isinstance(value, base.Source):

                # .. convert the whole section when the user asked
                # for it specifically.
                if converter:
                    value = converter.customize(value)

                # .. or otherwise add it to the subsections so that we
                # can gather all of them from all sources and put them
                # together into a new subconfig afterwards.
                else:
                    subsections.appendleft(source.get_root())
                    continue

            # the key was found and holds a normal value instead.
            else:
                if not source.is_typed():
                    value = self._get_typed_value(key, value)

                if converter:
                    value = converter.customize(value)

            # the key was either a normal value or a subsection that was
            # converted to a custom object. In both cases we still apply
            # a strategy if the user set one. If the user did specify
            # one this also means we will continue looking for the key
            # in other sources, too. Therefore we are not returning the
            # value just yet.
            if strategy:
                result = strategy(result, value)
            else:
                return value

        # we exited the for-loop without returning a value because..
        # .. the user specified a strategy so that we had to iterate
        # all sources.
        if strategy:
            return result
        # .. or the key held a subsection and we have to convert them to
        # a subconfig.
        elif subsections:
            return self._make_subconfig(subsections, key)
        # .. or the key really wasn't found at all.
        else:
            raise KeyError("Key '%s' was not found" % key)

    def __setitem__(self, key, value):
        for source in self.source_list:
            if key in source:
                source[key] = value
                return

        # no source was found so write it to first writable source
        for source in self.source_list.writable():
            source[key] = value
            return

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

    # internal api
    # ============
    def _read(self):
        # not yet used due to refactorings. Probably we can move actual
        # traversing here. However that might conflict with the initial
        # intention to load the whole dictionary. Having lots of sources
        # might then be problematic.
        pass

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
                             parent=self,
                             keychain=self._keychain+(key,),
                             strategy_map=self.strategy_map,
                             converters=self._converters
                             )


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
