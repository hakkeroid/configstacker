configstacker
=============

What is it?
-----------

Configstacker is a python library that aggregates different configuration
sources (e.g. files, environment variables, remote services like etcd)
into a simple object that can be accessed like a dictionary or with
dot-notation. Additionally it allows to specify custom type conversions
and merging strategies for keys that occur in multiple sources.

.. code-block:: python

    from configstacker import StackedConfig
    from configstacker.sources import Environment, EtcdStore, YAMLFile

    # order of sources defines search priority
    config = StackedConfig(
        YAMLFile('/path/to/my/config.yml'),
        # untyped sources gets type information from typed sources
        EtcdStore('https://my-etcd-host/'),
        Environment(prefix='MYAPP')
    )

    # simple dot-notation access
    assert config.a_key == True

    # dictionary access
    assert config['subsection'].nested_key == 100

    # dumping on any level
    assert config.dump() == {'a_key': True, 'subsection': {'nested_key': 100}}
    assert config.subsection.dump() == {'nested_key': 100}
    

Latest Version and History
--------------------------

Configstacker adheres to `Semantic Versioning <http://semver.org/>`_.

The current version is 0.1.0 which means configstacker is still in
a planning phase. As such it is *not meant for production use*. That
said it is already very stable and should hit its first major version
soon.

Changes can be found in `CHANGELOG <CHANGELOG.md>`_.

Installation
------------

Configstacker can be installed with pip and only requires
`six <https://pypi.python.org/pypi/six>`_.

.. code::

    pip install configstacker

However, some of the configuration sources require additional packages
to be installed when in use.

 * `YAMLFile` requires `pyyaml <https://pypi.python.org/pypi/PyYAML>`_
 * `EtcdStore` requires `requests <https://pypi.python.org/pypi/requests/2.13.0>`_

You can use the following syntax to install all optional dependencies. 

.. code::

    pip install configstacker[yaml,etcd]


Licensing
---------

Please see `LICENSE <LICENSE>`_.


Contribution
------------

Contributions are very welcome. Please file any bugs or issues on 
`github <https://github.com/hakkeroid/configstacker>`_ or 
`gitlab <https://gitlab.com/hakkeroid/configstacker>`_.
