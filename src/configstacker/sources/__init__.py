# -*- coding: utf-8 -*-

"""
This package contains all builtin source loaders. As every source loader
has its own submodule with all neccessary implementations this package
provides a unified access interface. However, for users of configstacker
it is recommended to use the :ref:`configstacker` package to access
source loaders instead as this subpackage might change and probably
become a private package.
"""

from .base import Source
from .dictsource import DictSource
from .environment import Environment
from .etcdstore import EtcdStore
from .inifile import INIFile
from .jsonfile import JSONFile
from .stacker import StackedConfig, SourceList
from .yamlfile import YAMLFile
