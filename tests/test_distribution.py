# -*- coding: utf-8 -*-

import pkg_resources
import pytest

SOURCE_FILE_MAP = {
    'yaml': 'YAMLFile',
    'etcd': 'EtcdStore',
}

DIST = pkg_resources.get_distribution('configstacker')

@pytest.fixture(params=DIST.extras)
def dependencies(request):
    extra = request.param
    source = SOURCE_FILE_MAP[extra]
    requirements = DIST.requires(extras=[extra])[1:]

    yield extra, source, requirements


def test_dependencies(dependencies):
    extra, source, requirements = dependencies

    for requirement in requirements:
        installed = pkg_resources.working_set.find(requirement)
        if not installed:
            with pytest.raises(ImportError) as exc_info:
                from configstacker import sources
                getattr(sources, source)('some source')

            assert 'optional dependency' in str(exc_info.value)
