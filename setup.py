#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from setuptools import setup, find_packages

REQUIREMENTS = [
    'six',
]

EXTRA_REQUIREMENTS = {
    'yaml': ['pyyaml'],
}


with open('README.rst') as file:
    long_description = file.read()


setup(
    name='configstacker',
    version='0.1.0',
    description='Aggregates multiple configuration sources into one '
                'configuration object with dot-notation or '
                'dictionary-like access.',
    long_description=long_description,
    author='Philipp Busch',
    author_email='hakkeroid@philippbusch.de',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    license="BSD",
    zip_safe=False,
    keywords='configuration multi stacked configs',
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
    extras_require=EXTRA_REQUIREMENTS
)
