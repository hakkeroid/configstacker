Advanced Use Cases
==================

.. _advanced-converters:

Providing Type Converters
-------------------------

When working with untyped sources like INI files or environment
variables there are a few approaches to convert values to the correct
type.

    1. Guess a type based on the content
    2. Distill information from other sources
    3. Manually provide type information for each key

Each approach has is pros and cons, ranging from either more failures to
otherwise more manual labor. Because failures are inacceptable only the
the second approach will be applied whenever possible and everything
else stays untouched. However, configstacker makes it fairly easy for
you to provide additional information to convert values.

Converters for Specific Keys
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Consider the following setup.

.. testcode::

    import os
    import configstacker as cs

    os.environ['MYAPP|SOME_NUMBER'] = '100'
    os.environ['MYAPP|SOME_BOOL'] = 'False'
    os.environ['MYAPP|NESTED|SOME_BOOL'] = 'True'

    untyped_env = cs.Environment('MYAPP', subsection_token='|')

Accessing the values will return them as strings because configstacker
has no other source of knowledge.

.. doctest::

    >>> type(untyped_env.some_number)
    <class 'str'>

To solve that issue we can provide a list of :any:`converters
<api/configstacker.converters>`. A converter consists of a value name
and two converter functions. One that turns the value into the expected
format (here ``int``) and another one that turns it back to a storable
version like ``str``.

.. testcode::

    converter_list = [
        cs.Converter('some_number', int, str)
    ]
    partly_typed_env = cs.Environment('MYAPP', converters=converter_list, subsection_token='|')

Now accessing ``some_number`` will return it as an integer while
``some_bool`` is still a string.

.. doctest::

    >>> partly_typed_env.some_number
    100
    >>> type(partly_typed_env.some_number)
    <class 'int'>

To also convert the boolean value we could just compare the value to
strings and return the result.

.. testcode::

    def to_bool(value):
        return value == 'True'

    assert to_bool('True')

However, that is not very safe and we should be a bit smarter about it.
So more elaborate versions might even use other libraries to do the heavy
lifting for us. 

.. testcode::

    import distutils

    def to_bool(value):
        return bool(distutils.util.strtobool(value))

    assert to_bool('yes')

After we choose an approach let's put everything together. For
convenience we can provide the converters as simple tuples.
Configstacker will convert them internally. Just make sure to stick to
the correct order of elements. First the key to convert, then the
customizing function and finally the resetting function.

.. testcode::

    converter_list = [
        ('some_bool', to_bool, str),
        ('some_number', int, str),
    ]
    typed_env = cs.Environment('MYAPP', converters=converter_list, subsection_token='|')

Now all values including the nested ones are typed. Also the value assignment
works as expected.

.. doctest::

    >>> typed_env.some_number
    100
    >>> typed_env.some_bool
    False
    >>> typed_env.some_bool = True
    >>> typed_env.some_bool
    True
    >>> typed_env.some_bool = 'False'
    >>> typed_env.some_bool
    False
    >>> typed_env.nested.some_bool
    True

Converters With Wildcards
~~~~~~~~~~~~~~~~~~~~~~~~~

The previous method only works if you know the value names in advance.
Consider we have a simple map of libraries with their name and version
string. 

.. testcode::

    DATA = {
        'libraries': {
            'six': '3.6.0',
            'requests': '1.2.1',
        }
    }

When accessing a library it would be really nice to get its
version as a named tuple rather then a simple string. The issue is that
we don't want to specify a converter for each library. Instead we can
make use of a wildcard to apply a converter to all matching keys. Let's
first create the version class and its serializers.

.. testcode::

    import collections

    Version = collections.namedtuple('Version', 'major minor patch')

    def to_version(version_string):
        parts = version_string.split('.')
        return Version(*map(int, parts))

    def to_str(version):
        return '.'.join(map(str, version))

With that in place we can create our config object with a converter that
uses a wildcard to match all nested elements of `libraries`.

.. testcode::

    import configstacker as cs 

    config = cs.DictSource(DATA, converters=[
        ('libraries.*', to_version, to_str)
    ])

Now we can access a library by its name and get a nice version object
returned.

.. doctest::

    >>> config.libraries.six
    Version(major=3, minor=6, patch=0)
    >>> config.libraries.requests.major
    1


It is important to understand that changing a value on the converted
object will not be stored in the configuration automatically. This is
because configstacker doesn't know when the custom object changes. To
save changes to the object you can simply reassign it to the same key
that you used to access it in the first place. You can also assign the
object to a new key as long as it is covered by a converter or the
underlying source handler is capable of storing it.

.. note::

    The previous example only show cased the idea. For real use cases
    you should probably use a library that knows how to properly handle
    versions strings.

Converting Lists
~~~~~~~~~~~~~~~~

In the previous section we had a very simple data dictionary where all
libraries consisted of a name-to-version mapping. In this example we
will have a list of json-like objects instead. The information is the
same as before. Each item consists of a name and version pair.

.. code-block:: python

    DATA = {
        'libraries': [{
            'name': 'six',
            'version': '3.6.0',
        }, {
            'name': 'request',
            'version': '1.2.0',
        }]
    }

Equally we will setup our classes and serializers first. Also we assume
a very simple version bump logic where a major update will reset the
minor and patch numbers to zero and a minor upate resets the patch
number to zero.

.. code-block:: python

    import collections
    import configstacker as cs
    import six

    Version = collections.namedtuple('Version', 'major minor patch')

    class Library(object):
        def __init__(self, name, version):
            self.name = name
            self.version = version

        def bump(self, part):
            major, minor, patch = self.version
            if part == 'major':
                new_parts = major + 1, 0, 0
            elif part == 'minor':
                new_parts = major, minor + 1, 0
            elif part == 'patch':
                new_parts = major, minor, patch + 1
            else:
                raise ValueError('part must be major, minor or patch')
            self.version = Version(*new_parts)

Because configstacker doesn't know anything about the type of the values
it has no idea how to treat lists. Especially how to parse and iterate
over the individual items. So instead of just creating converter
functions for single items we additionally have to create wrappers to
convert and reset the whole list.

.. code-block:: python

    def _load_library(library_spec):
        version_parts = library_spec['version'].split('.')
        version = Version(*map(int, version_parts))
        return Library(library_spec['name'], version)

    def load_list_of_libraries(library_specifications):
        """Convert list of json objects to Library objects."""
        return [_load_library(specification) for specification in library_specifications]

    def _dump_library(library):
        version_str = '.'.join(map(str, library.version))
        return {'name': library.name, 'version': version_str}

    def dump_list_of_libraries(libraries):
        """Dump list of Library objects to json objects."""
        return [_dump_library(library) for library in libraries]


The final config object will be created as follows:

.. code-block:: python

    config = cs.DictSource(DATA, converters=[
        ('libraries', load_list_of_libraries, dump_list_of_libraries)
    ])

Converting Subsections
~~~~~~~~~~~~~~~~~~~~~~

Usually a subsection, or a nested dict in python terms, is handled in
a special way as it needs to be converted into a configstacker instance.
However, you can change that behavior by providing a converter for
a subsection. This is useful if you want to use the nested information
to assemble a larger object or only load an object if it is accessed.

As an example consider we have a todo application that stores todos in
a database, a caldav resource or anything else. To keep the application
flexible it needs to be ignorant to how the storage system works
internally but it has to know about how it can be used. For that reason
the storage should implement an interface that is known to the
application. Also it shouldn't be hardcoded into the application but
injected into it at start or runtime. With this setup it is pretty
simple for the user to specify which storage to use and how it should be
configured. When starting the application we will then dispatch the
configuration to the specific storage factory and assemble it there.

The next snippet contains the interface ``IStorage`` that enforces the
existence of a ``save`` and a ``get_by_name`` method. Additionally you
will find two dummy implementations for a database and a caldav storage.

.. code-block:: python

    import abc

    class IStorage(abc.ABC):

        @abc.abstractmethod
        def save(self, todo):
            pass

        @abc.abstractmethod
        def get_by_name(self, name):
            pass

    class DB(IStorage):
        def __init__(self, user, password, host='localhost', port=3306):
            # some setup code
            self.host = host

        def get_by_name(self, name):
            # return self._connection.select(...)
            pass

        def save(self, todo):
            # self._connection.insert(...)
            pass

        def __repr__(self):
            return '<DB(host="%s")>' % self.host

    class CalDav(IStorage):
        def __init__(self, url):
            # some setup code
            self.url = url

        def get_by_name(self, name):
            # return self._resource.parse(...)
            pass

        def save(self, todo):
            # self._resource.update(...)
            pass

        def __repr__(self):
            return '<CalDav(url="%s")>' % self.url

The following two json files are examples of how a storage configuration
could look like. They are following a simple convention. ``type`` is the
class that should be loaded while the content of the optional ``setup``
key will be passed to the class on instantiation.

.. code-block:: json

    {
      "storage": {
        "type": "DB",
        "setup": {
          "user": "myuser",
          "password": "mypwd"
        }
      }
    }

.. code-block:: json

    {
      "storage": {
        "type": "CalDav",
        "setup": {
          "url": "http://localhost/caldav.php"
        }
      }
    }

First let's continue without a converter to see the difference between
both versions. We read the config files as usual and assemble a storage
object with the respective class from the ``storage_module``. Finally
it gets injected into the todo application.

.. code-block:: python

    import configstacker as cs
    import storage_module

    config = cs.YAMLFile('/path/to/config.yml')
    storage_class = getattr(storage_module, config.storage.type)
    storage = storage_class(**config.storage.get('setup', {}))

    app = TodoApp(storage)

To make the code cleaner we could refactor the storage related setup
into its own function and assign it to a converter instead.

.. code-block:: python

    import configstacker as cs
    import storage_module

    def load_storage(spec):
        storage_class = getattr(storage_module, spec.type)
        return storage_class(**spec.get('setup', {}))

    config = cs.YAMLFile('/path/to/config.yml',
                         converters=[('storage', load_storage, None)])

    app = TodoApp(config.storage)

With the converter in place accessing the storage returns us a fully
constructed storage object instead of a nested subsection.

.. code-block:: python

    >>> config.storage
    <CalDav(url="http://localhost/caldav.php")>


.. _advanced-merging:

Using Merge Strategies
----------------------

Often configurations are meant to override each other depending on their
priority. However, there are cases where consecutive values should not
be overridden but handled differently, for example collected into
a list.

Consider we are building a tool that allows to specify multiple paths.
For that we want to define a set of default paths and enable our users
to add additional paths if they want to.

.. testcode::

    import os
    import configstacker as cs

    # our predefined defaults
    DEFAULTS = {
        'path': '/path/to/default/file'
    }
    # a user set variable
    os.environ['MYAPP|PATH'] = '/path/to/user/file'

    config = cs.StackedConfig(
        cs.DictSource(DEFAULTS),
        cs.Environment('MYAPP', subsection_token='|'),
    )

When we try to access ``path`` we will only get the value from the
source with the highest priority which in this case is the environment
variable.

.. doctest::

    >>> config.path
    '/path/to/user/file'

To solve this problem we can use a merge strategy that simply collects
all values into a list. For that we create a strategy map which contains
the value's name and its merge function. All occurrences of the
specified key will now be merged consecutively **with the previous merge
result**.

.. testcode::

    config = cs.StackedConfig(
        cs.DictSource(DEFAULTS),
        cs.Environment('MYAPP', subsection_token='|'),
        strategy_map={
            'path': cs.strategies.collect
        }
    )

Here we use :any:`collect` which is one of the :any:`builtin strategies
<api/configstacker.strategies>` and perfectly fits our needs. Now when
we access ``path`` it returns a list of values in the prioritized order.

.. doctest::

    >>> config.path
    ['/path/to/user/file', '/path/to/default/file']

Let's say instead of merging the paths into a list we want to join all
paths with a colon (or semicolon if you are on Windows). Create
a function that accepts a ``previous`` and a ``next_`` parameter and
join both values together.

.. testcode::

    def join_paths(previous, next_):
        if previous is cs.strategies.EMPTY:
            return next_

        return ':'.join([previous, next_])

    assert join_paths(cs.strategies.EMPTY, '/a/path') == '/a/path'
    assert join_paths('/a/path', '/other/path') == '/a/path:/other/path'

Some things to note:

    - ``next_`` ends with an underscore to prevent name clashes with the
      builtin :any:`next() <next>` function.
    - When the merge function is called ``previous`` contains the result
      from the last call and ``next_`` contains the current value.
    - If the merge function is called for the first time configstacker
      will pass :any:`EMPTY` to ``previous``. This is a good time to
      return a default value which in our case is ``next_``.

To have something to play with we will also access the system
environment variables so that we can make use of our global path variable.
To not accidentally change anything we will load them in a read-only mode.

.. testcode::

    config = cs.StackedConfig(
        cs.Environment('', readonly=True),
        cs.DictSource(DEFAULTS),
        cs.Environment('MYAPP', subsection_token='|'),
        strategy_map={
            'path': join_paths
        }
    )
    
``path`` should now return a single string with the user defined path,
the default path and the system path joined together with a colon.

.. doctest::

    >>> config.path
    '/path/to/user/file:/path/to/default/file:/...'

.. warning::

    This is a demonstration only. Be extra cautious when accessing the
    system variables like that.

.. note::

    When using an empty prefix to access the system variables understand
    that ``MYAPP`` variables will also show up unparsed as ``myapp|...``
    in the config object. This is because the source handler with the
    empty prefix doesn't know anything about the special meaning of
    ``MYAPP``.


.. _advanced-extending:

Extending Source Handlers
-------------------------

Configstacker already ships with a couple of source handlers. However,
there are always reasons why you want to override an existing handler or
create a completely new one. Maybe the builtin handlers are not working
as required or there are simply no handlers for a specific type of source
available.

Therefore configstacker makes it fairly easy for you to create new
handlers. You only have to extend the base :any:`Source` class and
create at least a :any:`_read() <Source._read>` method that returns
a dictionary. If you also want to make it writable just add
a :any:`_write(data) <Source._write>` method which in return accepts
a dictionary and stores the data in the underlying source.

Assume you want to read information from a command line parser. There
are a couple of ways to accomplish that. The easiest one would be to
handover already parsed cli parameters to configstacker as
a :any:`DictSource` which is readonly and has the highest priority in
a stacked configuration. This method is great because it allows us to
easily incorporate any cli parser you like. It just has to return
a dictionary. Another way would be to create a parser that hooks into
:any:`sys.argv` and strips out the information itself. For demonstration
purposes we will implement the latter case.

.. note::

    Handling the cli is a complex task and varies greatly between
    applications and use cases. As such there is no default cli
    handler integrated into configstacker.
    If you are building a cli for your application it is probably
    easier to just go with the ``DictSource`` approach and make use of
    great tools like `click <http://click.pocoo.org>`_.

The following handler will create an :any:`argparse.ArgumentParser`
internally. Because cli parameters cannot be changed after the script or
application has been started we don't need a ``_write`` method to save
changes. Additionally because they are only entered once at the startup
of the application we also don't need to lazy load them. Therefore the
arguments can already be parsed in the ``__init__`` method which makes
``_read`` very simple.

.. literalinclude:: cookbook/cli-source.py

We can test it by invoking our handler and providing some arguments to
it.

.. doctest::

    >>> cfg = CliSource(['-vv', 'some_job'])
    >>> cfg.name
    'some_job'
    >>> cfg.verbose
    2
    >>> cfg.index.cache
    False

Now let's call it as a script to make use of the exemplary main
function. It will show us the help.

.. code-block:: console
    
    $ python cli-source.py -h
    usage: cli-source.py [-h] [--job-cache] [-r JOB_RETRIES] [--host-url HOST_URL]
                         [--host-port HOST_PORT] [-v]
                         job_name

    positional arguments:
      job_name

    optional arguments:
      -h, --help            show this help message and exit
      --job-cache
      -r JOB_RETRIES, --job-retries JOB_RETRIES
      --host-url HOST_URL
      --host-port HOST_PORT
      -v, --verbose

And finally run a pseudo job.

.. code-block:: console

    $ python cli-source.py -vv some_job
    Job runner:     localhost:5050
    Job cache:      disabled
    Max retries:    0
    Start job some_job
