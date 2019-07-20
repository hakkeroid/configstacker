configstacker
=============

.. start-introduction

.. image:: https://gitlab.com/hakkropolis/configstacker/badges/v0.1.0/pipeline.svg
    :alt: pipeline status
    :target: https://gitlab.com/hakkropolis/configstacker/commits/v0.1.0

.. image:: https://gitlab.com/hakkropolis/configstacker/badges/v0.1.0/coverage.svg
    :alt: coverage report
    :target: https://gitlab.com/hakkropolis/configstacker/commits/v0.1.0


What is configstacker?
----------------------

Configstacker is a python library with the goal to simplify
configuration handling as much as possible. You can read configurations
from different sources (e.g. files, environment variables and others)
and load single or merge multiple sources at will. The resulting
configuration object can be used like a dictionary or with dot-notation.
If you need additional flexibility configstacker also allows you to
specify converters for values or merging strategies for keys that occur
multiple times throughout different sources. If this is still not
sufficient enough configstacker makes it very easy for you to add
additional source handlers.

.. code-block:: python
    :name: single-source-example

    #
    # Single Source Example
    #
    from configstacker import YAMLFile

    config = YAMLFile('/path/to/my/config.yml')

    # Dot-notation access
    assert config.a_key is True

    # Mixed dictionary and dot-notation access
    assert config['subsection'].nested_key == 100

    # Dictionary-like interface
    assert config.keys() == ['a_key', 'subsection']

    # Dictionary dumping on any level
    assert config.dump() == {'a_key': True, 'subsection': {'nested_key': 100}}
    assert config.subsection.dump() == {'nested_key': 100}

    # New value assignment
    config.new_value = 10.0
    assert config.new_value == 10.0


.. code-block:: python
    :name: multi-source-example

    #
    # Multi Source Example
    #
    import configstacker as cs

    # The resulting configuration object behaves
    # the same as a single source one.
    config = cs.StackedConfig(
        # The order of sources defines their search priority whereas the
        # last element has the highest one.
        cs.Environment(prefix='MYAPP'),
        cs.YAMLFile('/path/to/my/config.yml')
    )

    # Higher priority values shadow lower priority values.
    assert config.a_key is False

    # Lower prioritized values which are not shadowed stay accessible.
    assert config['subsection'].nested_key == 100

    # New values will be added to the source that has the highest
    # priority and is writable.
    config.other_new_value = True
    assert config.other_new_value is True

    # In this case the new item was added to the last element in the
    # source list.
    assert config.source_list[-1].other_new_value

.. stop-introduction

Examples for type conversion and merging strategies can be found in the
`documentation <http://configstacker.readthedocs.io/advanced>`_.


Latest Version and History
--------------------------

.. start-version

Configstacker adheres to `Semantic Versioning <http://semver.org/>`_.

The current version is 0.1.0 which means configstacker is still in
a planning phase. As such it is *not meant for production use*. That
said it is already very stable and should hit its first major version
soon.

.. stop-version

Changes can be found in `CHANGELOG <CHANGELOG.md>`_.


.. start-installation

Installation
------------

Configstacker can be installed with pip and only requires
`six <https://pypi.python.org/pypi/six>`_ for the minimal installation.

.. code::

    pip install configstacker

However, some of the source handlers require additional packages when in
use.

 * `YAMLFile` requires `pyyaml <https://pypi.python.org/pypi/PyYAML>`_

You can use the following syntax to install all optional dependencies.
Leave out those from the brackets you do not need.

.. code::

    pip install configstacker[yaml]

.. note::

    New source handlers with additional dependencies might be added over
    time.

.. stop-installation


Documentation
-------------

Configstacker provides a `user documentation <https://configstacker.readthedocs.io/>`_
on `readthedocs.org <https://readthedocs.org/>`_.


Licensing
---------

Please see `LICENSE <LICENSE>`_.


Contribution
------------

Contributions are very welcome. The main development happens on
`gitlab <https://gitlab.com/hakkropolis/configstacker/issues>`_. For reporting
issues you can also use `github <https://github.com/hakkeroid/configstacker/issues>`_.
