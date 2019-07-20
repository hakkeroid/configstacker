#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

REQUIREMENTS = [
    'six',
]

EXTRA_REQUIREMENTS = {
    'yaml': ['pyyaml'],
}

PYTHON_REQUIREMENTS = ','.join([
    '>=2.7',
    '!=3.0.*',
    '!=3.1.*',
    '!=3.2.*',
    '!=3.3.*'
])

with open('README.rst') as file:
    long_description = file.read()


setup(
    name='configstacker',
    version='0.1.1',
    description='Aggregates multiple configuration sources into one '
                'configuration object with dot-notation or '
                'dictionary-like access.',
    long_description=long_description,
    author='Philipp Busch',
    author_email='hakkeroid@philippbusch.de',
    url='https://gitlab.com/hakkropolis/configstacker',
    project_urls={
        'Bug Tracker': 'https://gitlab.com/hakkropolis/configstacker/issues',
        'Documentation': 'https://configstacker.readthedocs.io',
        'Source Code': 'https://gitlab.com/hakkropolis/configstacker/',
    },
    documentation="https://configstacker.readthedocs.io",
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    license="BSD-3-clause",
    zip_safe=False,
    keywords='configuration hierarchy multi stacked configs',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries',
    ],
    install_requires=REQUIREMENTS,
    extras_require=EXTRA_REQUIREMENTS,
    python_requires=PYTHON_REQUIREMENTS
)
