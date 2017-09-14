# -*- coding: utf-8 -*-

# make modules available on simple configstacker import
from . import strategies, converters, utils

# make sources available on root package for convenience
from .sources import (DictSource, Environment, EtcdStore, INIFile, JSONFile,
                      Source, StackedConfig, YAMLFile)
