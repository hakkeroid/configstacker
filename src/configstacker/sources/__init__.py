# -*- coding: utf-8 -*-

"""
This package contains all builtin source loaders. As every source loader
has its own submodule with all neccessary implementations this package
provides a unified access interface. However, for users of configstacker
it is recommended to use the :ref:`configstacker` package to access
source loaders instead as this subpackage might change and probably
become a private package.
"""

from .base import Source  # noqa: F401
from .dictsource import DictSource  # noqa: F401
from .environment import Environment  # noqa: F401
from .inifile import INIFile  # noqa: F401
from .jsonfile import JSONFile  # noqa: F401
from .stacker import SourceList, StackedConfig  # noqa: F401
from .yamlfile import YAMLFile  # noqa: F401
