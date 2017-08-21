Quickstart
==========

For simple use cases the :ref:`introductory examples <single-source-example>`
contains essentially everything that is required for simple use cases.
However, let's create a more elaborate example by providing some real
configuration sources that we can play with.

.. note::

    The following code snippets are either simple code blocks which you
    can copy and paste or interactive shell like code blocks with
    a ``>>>`` or ``$`` symbol to demonstrate example usages.

.. note::

    If you want to skip parts of the quickstart guide be aware that the
    examples depend on eachother.


.. _quickstart-preparation:

Preparation
-----------

First create a JSON file named :download:`config.json
<_static/config.json>` with the following content:

.. literalinclude:: _static/config.json

Because JSON files have the same structure as Python's dictionaries a
configuration object generated from the above file contains exactly the
same tree of keys and values as the file itself. Additionally the json
format stores type information which means that the parsed values will
already be converted to the respective type (e.g string, boolean,
number). Before jumping into the code let's create another file. This
time it is an INI file named :download:`config.ini <_static/config.ini>`
with the following content:

.. literalinclude:: _static/config.ini

By default Python's builtin configparser does not provide any
hierarchical information which means there are no concepts like root
level keys and subsections. To solve that issue configstacker implements
a common flavor of INI file formats which use a separator in their
section names to denote a hierarchy. Also the builtin configparser
requires that all keys belong to a section. Because of that we need
a special name to differentiate root level keys from subsection keys. To
summarize:

- The root level is indicated by a specially named section. By default
  it is called ``[__root__]``.
- Subsections are denoted by separators inside section names. The
  default separator is a dot.

Finally it is important to note that INI files do not store type
information. As such all values on a configuration object will be
returned as strings. This can be solved in two ways. We can either make
use of a :ref:`stacked configuration <quickstart-using-stacked-sources>`
with at least one other source that contains type information or we
provide :ref:`converters <advanced-converters>`.

.. note::

    The conventions used here are just the way how the INI file source
    handler shipped with configstacker works. Of course you can create
    your own INI file handler which uses another format. For example
    double brackets for subsections. However, in this case you also have
    to provide the respective parser as python's builtin configparser
    does not support this format.

Now that everything is prepared we can import and setup configstacker
itself. We will start by setting up a single source and playing around
with it. After that we will put everything together into a stacked
configuration.


.. _quickstart-using-single-sources:

Using Single Sources
--------------------

.. testsetup::

    import os
    #os.chdir('source/_static')

Make sure you are in your (virtual) environment where you installed
configstacker and open up your interactive python shell. Start with
importing configstacker and instantiating a :any:`JSONFile` object with
the path pointing to the JSON file you created earlier.

.. testcode::

    import configstacker as cs
    json = cs.JSONFile('config.json')

Without much surprise you should be able to access the information from
the JSON file.

.. doctest::

    >>> json.simple_int
    10
    >>> json.a_bool
    False
    >>> json.nested.a_float
    2.0

Let's look at a more interesting case - the INI file.

.. testcode::

    ini = cs.INIFile('config.ini', subsection_token='.')

.. note::

    The ``subsection_token`` is already a dot by default and only set
    for demonstration purpose.

You can access it the same way as with the JSON object.

.. doctest::

    >>> ini.simple_int
    '5'
    >>> ini.a_bool
    'True'
    >>> ini.section.some_float
    '0.1'
    >>> ini
    INIFile({...})

There are two things to note here:

- As mentioned earlier due to the untyped nature of INI files the
  returned values are always strings.
- When you print the whole config object it will show you the type of
  source and its content.

You can always use dictionary style to access the values. This is
especially important when a key has the same name as a builtin function.

.. doctest::

    >>> ini['simple_int']
    '5'
    >>> ini['section']['some_float']
    '0.1'
    >>> ini['keys']
    '1,2,3'
    >>> ini.keys()
    ['a_bool', 'keys', 'section', 'simple_int']

Although configuration objects behave like dictionaries in some cases
you might still want to use a real python dictionary. Therefore you can
easily dump the data from any sublevel.

.. doctest::

    >>> type(ini.dump())
    <class 'dict'>
    >>> ini.section.dump() == {'some_float': '0.1', 'subsection': {'some_string': 'A short string'}}
    True
    >>> ini.section.subsection.dump()
    {'some_string': 'A short string'}


.. _quickstart-using-stacked-sources:

Using Stacked Sources
---------------------

Now let's have a look at stacked configurations. When stacking source
handlers their order defines how keys and values are prioritized while
searching and accessing them. By default the last element has the
highest priority. This behavior can be changed though.

.. testcode::

    # We are reusing the configuration objects from the last examples
    config = cs.StackedConfig(json, ini)

.. note::

    The idea behind the default ordering is that you usually start with
    some global defaults which have the lowest priority and further
    advance to more specific configuration sources with a higher
    priority until you finally reach the last and most important one.

Let's access the data again and check what it looks like:

.. doctest::

    >>> config.simple_int
    5
    >>> config.a_bool
    True
    >>> config.section.some_float
    '0.1'
    >>> config.nested.dump()
    {'a_float': 2.0}

Some observations:

- The ``config`` object behaves exactly like the single source object.
  In fact both the stacked and the single source configuration objects
  provide the same dictionary interface and you can use them
  interchangeably. 
- ``simple_int`` is 5 and not 10 as the INI file has a higher
  priority over the JSON file. However, now that there is another source
  with type information available the value from the INI file was
  converted to an integer. This works because configstacker will search
  other sources for a typed version of the same key and converts it
  accordingly.
- ``some_float`` is still untyped as there is no counterpart in
  the JSON file.
- Because the INI file is lacking a ``nested`` section it is not
  shadowing the JSON file here and as such we have access to some data
  from the lower prioritized JSON file.


.. _quickstart-changing-behavior:

Changing Behavior of Stacked Sources
------------------------------------

Now let us create some environment variables to play with. As with
INI files environment variables also lack any hierarchical information.
However we can fix that the same way as we did with INI files by
decoding subsections into the variable names. Therefore we will use:

- the prefix *MYAPP* to indicate data related to our app.
- a pipe as a separator for nested sections. 
- an underscore as a separator for phrases as we did in our last examples.

.. testcode::

    import os

    os.environ['MYAPP|SIMPLE_INT'] = '-10'
    os.environ['MYAPP|SECTION|SOME_FLOAT'] = '3.5'

.. note::

    Usually it is recommended to only use alphanumeric characters and
    underscores for environment variables to prevent problems with less
    capable tools. However, using just one special character means we
    can't differentiate between the separation of subsections and phrases.
    It is up to you to decide whether you can ignore such less capable
    tools or not.

Stacked configuration sources can be modified at any time so that we can
easily integrate additional source handlers. Therefore
:any:`StackedConfig` exposes a :any:`SourceList` object which behaves
like a python list.

First create the environment source itself. Then integrate it with the
stacked configuration object.

.. testcode::

    env = cs.Environment('MYAPP', subsection_token='|')

    # appending it to the end gives it the highest priority
    config.source_list.append(env)

Now we can access the information as we did before:

.. doctest::

    >>> config.a_bool
    True
    >>> config.simple_int
    -10
    >>> config.section.some_float
    '3.5'

How are the values generated?

    - ``a_bool`` contains the value from INI file which then has been
      converted with type information from the JSON file.
    - ``simple_int`` contains the value from the newly added
      environment variables and was converted with type information
      from the JSON file.
    - ``some_float`` contains the value from the environment
      variables as it is higher prioritized than the INI file. However
      because there is no counterpart in the JSON file it is returned as
      a string.


.. _quickstart-persisting-changes:

Persisting Changes
------------------

In most cases changing values of a configuration is straight forward as
it does not require any special setup. We can simply assign the new
value to the respective key.

.. doctest::

    >>> config.a_bool = False
    >>> config.a_bool
    False

That also works with keys which do not yet exist.

.. doctest::

    >> config.new_value = 5
    >> config.new_value
    5

The following rules are applied to decide where to store changes.

    - Newly added key-value pairs are written to the highest priority
      source that is writable.
    - Changes to existing values are written to the highest priority
      source that is writable and where the respective keys were found.
    - If no writable source was found a TypeError is raised when
      changing a value.

.. note::

    If you want to protect a source from beeing changed at all you can
    provide the parameter :any:`readonly=True <Source>` when
    instantiating the source. However, if you just want to prevent
    immediate writes to the underlying source (e.g. because of network
    connectivity) you can make use of the :any:`cache functionality
    <Source.write_cache>`.
