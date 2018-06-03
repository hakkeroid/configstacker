# -*- coding: utf-8 -*-

"""
With the help of configstacker you can easily access configurations from
various sources.

The root package of configstacker provides everything you need to make
use of configstacker. It contains all the builtin source loaders which
are:

    - :any:`DictSource`
    - :any:`Environment`
    - :any:`INIFile`
    - :any:`JSONFile`
    - :any:`YAMLFile`
    - :any:`StackedConfig` *(for stacking other source loaders)*


Additionally there is also the :any:`Source` class to subclass and
create additional source loaders and :any:`SourceList` to easily handle
the underlying list of sources that :any:`StackedConfig` will traverse.

Finally you will find the following modules in configstacker:

    - the :py:mod:`~configstacker.strategies` module contains different
      merge functions for use with a StackedConfig.
    - the :py:mod:`~configstacker.utils` module contains some general
      helpers with reoccuring patterns.

"""


# make modules available on simple configstacker import
from . import converters, strategies, utils  # noqa: F401
# make sources available on root package for convenience
from .sources import (DictSource, Environment, INIFile, JSONFile,  # noqa: F401
                      Source, SourceList, StackedConfig, YAMLFile)
