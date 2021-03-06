========
Tasks
========

Intro
-------

`doit` is all about automating task dependency management and execution.
Tasks can execute external shell commands/scripts or python functions
(actually any callable).
So a task can be anything you can code :)

Tasks are defined in plain `python <http://python.org/>`_ module with some
conventions.

.. note::

    You should be comfortable with python basics. If you don't know python yet
    check `Python tutorial <http://docs.python.org/tut/>`_.


A function that starts with the name `task_` defines a *task-creator* recognized
by `doit`.
These functions must return (or yield) dictionaries representing a *task*.
A python module/file that defines *tasks* for `doit` is called **dodo** file
(that is something like a `Makefile` for `make`).

Take a look at this example (file dodo.py):

.. literalinclude:: tutorial/hello.py

When `doit` is executed without any parameters it will look for tasks in a
file named `dodo.py` in the current folder and execute its tasks.


.. code-block:: console

  $ doit
  .  hello

On the output it displays which tasks were executed.
In this case the `dodo` file has only one task, `hello`.


Actions
--------

Every *task* must define **actions**.
It can optionally define other attributes like `targets`, `file_dep`,
`verbosity`, `doc` ...

Actions define what the task actually does.
*Actions* is always a list that can have any number of elements.
The actions of a task are always run sequentially.
There 2 basic kinds of `actions`: *cmd-action* and *python-action*.
The action "result" is used to determine if task execution was successful or not.


python-action
^^^^^^^^^^^^^^

If `action` is a python callable or a tuple `(callable, *args, **kwargs)`
- only `callable` is required.
The callable must be a function, method or callable object.
Classes and built-in functions are not allowed.
``args`` is a sequence and ``kwargs`` is a dictionary that will be used
as positional and keywords arguments for the callable.
see `Keyword Arguments <http://docs.python.org/tutorial/controlflow.html#keyword-arguments>`_.


The result of the task is given by the returned value of the ``action`` function.
So it must return a *boolean* value `True`, `None`,
a dictionary or a string to indicate successful completion of the task.
Use `False` to indicate task failed.
If it raises an exception, it will be considered an error.
If it returns any other type it will also be considered an error
but this behavior might change in future versions.

.. literalinclude:: tutorial/tutorial_02.py

The function `task_hello` is a *task-creator*, not the task itself.
The body of the task-creator function is always executed when the dodo
file is loaded.

.. note::

  The body of task-creators are executed even if the task is not going
  to be executed.
  The body of task-creators should be used to create task metadata only,
  not execute tasks!
  From now on when the  documentation says that a *task* is executed,
  read "the task's actions are executed".


cmd-action
^^^^^^^^^^^

CmdAction's are executed in a subprocess (using python
`subprocess.Popen <http://docs.python.org/library/subprocess.html#popen-constructor>`_).

If `action` is a string, the command will be executed through the shell.
(Popen argument shell=True).

Note that the string must be escaped according to
`python string formatting <http://docs.python.org/library/stdtypes.html#string-formatting-operations>`_.

It is easy to include dynamic (on-the-fly) behavior to your tasks with
python code from the `dodo` file. Let's take a look at another example:


.. literalinclude:: tutorial/cmd_actions.py

.. note::

  The body of the *task-creator* is always executed,
  so in this example the line `msg = 3 * "hi! "` will always be executed.


If `action` is a list of strings, by default it will be executed **without the shell** (Popen argument shell=False).

.. literalinclude:: tutorial/cmd_actions_list.py


For complex commands it is also possible to pass a callable that returns
the command string. In this case you must explicit import CmdAction.

.. literalinclude:: tutorial/cmd_from_callable.py


You might also explicitly import ``CmdAction`` in case you want to pass extra
parameters to ``Popen`` like ``cwd``.
All keyword parameter from ``Popen`` can be used on ``CmdAction`` (except
``stdout`` and ``stderr``).

.. note::

  Different from `subprocess.Popen`, `CmdAction` `shell` argument defaults to
  `True`. All other `Popen` arguments can also be passed in `CmdAction` except
  `stdout` and `stderr`



The result of the task follows the shell convention.
If the process exits with the value `0` it is successful.
Any other value means the task failed.


.. _custom-actions:

custom actions
^^^^^^^^^^^^^^^^^^^

It is possible to create other type of actions,
check :ref:`tools.LongRunning<tools.LongRunning>` as an example.



task name
------------

By default a task name is taken from the name of the python function
that generates the task.
For example a `def task_hello` would create a task named ``hello``.

It is possible to explicitly set a task name with the parameter ``basename``.

.. literalinclude:: tutorial/task_name.py


.. code-block:: console

  $ doit
  .  hello
  .  hello2


When explicit using ``basename`` the task-creator is not limited
to create only one task.
Using ``yield`` it can generate several tasks at once.
It is also possible to ``yield`` a generator that generate tasks.
This is useful to write some generic/reusable task-creators.

.. literalinclude:: tutorial/task_reusable.py

.. code-block:: console

  $ doit
  .  t2
  .  t1


sub-tasks
---------

Most of the time we want to apply the same task several times
in different contexts.

The task function can return a python-generator that yields dictionaries.
Since each sub-task must be uniquely identified it requires an
additional field ``name``.

.. literalinclude:: tutorial/subtasks.py


.. code-block:: console

    $ doit
    .  create_file:file0.txt
    .  create_file:file1.txt
    .  create_file:file2.txt



avoiding empty sub-tasks
^^^^^^^^^^^^^^^^^^^^^^^^^^

If you are not sure sub-tasks will be created for a given ``basename``
but you want to make sure that a task exist,
you can yield a sub-task with ``name`` equal to ``None``.
This can also used to set the task ``doc`` and ``watch`` attribute.

.. literalinclude:: tutorial/empty_subtasks.py

.. code-block:: console

  $ doit
  $ doit list
  do_x   docs for X



Dependencies & Targets
-------------------------

One of the main ideas of `doit` (and other build-tools) is to check if the
tasks/targets are **up-to-date**. In case there is no modification in the
dependencies and the targets already exist, it skips the task execution to
save time, as it would produce the same output from the previous run.

Dependency
  A dependency indicates an input to the task execution.

Target
  A *target* is the result/output file produced by the task execution.


i.e. In a compilation task the source file is a *file_dep*,
the object file is a *target*.

.. literalinclude:: tutorial/compile.py


`doit` automatically keeps track of file dependencies. It saves the
signature (MD5) of the dependencies every time the task is completed successfully.

So if there are no modifications to the dependencies and you run `doit` again.
The execution of the task's actions is skipped.


.. code-block:: console

  $ doit
  .  compile
  $ doit
  -- compile

Note the ``--`` (2 dashes, one space) on the command output on the second
time it is executed. It means, this task was up-to-date and not executed.

.. _file-dep:

file_dep (file dependency)
-----------------------------

Different from most build-tools dependencies are on tasks, not on targets.
So `doit` can take advantage of the "execute only if not up-to-date" feature
even for tasks that don't define targets.

Let's say you work with a dynamic language (python in this example).
You don't need to compile anything but you probably want to apply a lint-like
tool (i.e. `pyflakes <http://pypi.python.org/pypi/pyflakes>`_) to your
source code files. You can define the source code as a dependency to the task.


.. literalinclude:: tutorial/checker.py

.. code-block:: console

   $ doit
   .  checker
   $ doit
   -- checker

Note the ``--`` again to indicate the execution was skipped.

Traditional build-tools can only handle files as "dependencies".
`doit` has several ways to check for dependencies, those will be introduced later.


targets
-------

Targets can be any file path (a file or folder). If a target doesn't exist
the task will be executed. There is no limitation on the number of targets
a task may define. Two different tasks can not have the same target.

Lets take the compilation example again.

.. literalinclude:: tutorial/compile.py

* If there are no changes in the dependency the task execution is skipped.
* But if the target is removed the task is executed again.
* But only if it does not exist. If the target is modified but the dependencies
  do not change the task is not executed again.

.. code-block:: console

    $ doit
    .  compile
    $ doit
    -- compile
    $ rm main.o
    $ doit
    .  compile
    $ echo xxx > main.o
    $ doit
    -- compile


execution order
-----------------

If your tasks interact in a way where the target (output) of one task is a
file_dep (input) of another task, `doit` will make sure your tasks are
executed in the correct order.

.. literalinclude:: tutorial/taskorder.py

.. code-block:: console

  $ doit
  .  create
  .  modify



.. _task-selection:

Task selection
----------------


By default all tasks are executed in the same order as they were defined (the order may change to satisfy dependencies). You can control which tasks will run in 2 ways.

Another example

.. literalinclude:: tutorial/selecttasks.py

DOIT_CONFIG -> default_tasks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*dodo* file defines a dictionary ``DOIT_CONFIG`` with ``default_tasks``, a list of strings where each element is a task name.

.. code-block:: console

    $ doit
    .  t1
    .  t3

Note that only the task *t3* was specified to be executed by default.
But its dependencies include a target of another task (t1).
So that task was automatically executed also.


command line selection
^^^^^^^^^^^^^^^^^^^^^^^

From the command line you can control which tasks are going to be execute by passing its task name. Any number of tasks can be passed as positional arguments.

.. code-block:: console

    $ doit t2
    .  t2


You can also specify which task to execute by its target:

.. code-block:: console

    $ doit task1
    .  t1


sub-task selection
^^^^^^^^^^^^^^^^^^^^^

You can select sub-tasks from the command line specifying its full name.

.. literalinclude:: tutorial/subtasks.py


.. code-block:: console

    $ doit create_file:file2.txt
    .  create_file:file2.txt


wildcard selection
^^^^^^^^^^^^^^^^^^^^

You can also select tasks to be executed using a `glob <http://docs.python.org/library/glob.html>`_ like syntax (it must contains a ``*``).

.. code-block:: console

    $ doit create_file:file*
    .  create_file:file1.txt
    .  create_file:file2.txt
    .  create_file:file3.txt


.. _parameters:

arguments
-----------

It is possible to pass option parameters to the task through the command line.

Just add a ``params`` field to the task dictionary. ``params`` must be a list of
dictionaries where every entry is an option parameter. Each parameter must
define a name, and a default value. It can optionally define a "short" and
"long" names to be used from the command line (it follows unix command line
conventions). It may also specify additional attributes, such as
`type` and `help` (see :ref:`below <parameters-attributes>`).


See the example:

.. literalinclude:: tutorial/parameters.py


For python-actions the python function must define arguments with the same name as a task parameter.

.. code-block:: console

    $ doit py_params -p abc --param2 4
    .  py_params
    abc
    9

For cmd-actions use python string substitution notation:

.. code-block:: console

    $ doit cmd_params -f "-c --other value"
    .  cmd_params
    mycmd -c --other value xxx



.. _parameters-attributes:

All parameters attributes
^^^^^^^^^^^^^^^^^^^^^^^^^

Here is the list of all attributes ``param`` accepts:

``name``
    Name of the parameter, identifier used as name of the the parameter
    on python code.
    It should be unique among others.

    :required:  True
    :type:      `str`

``default``
    Default value used when it is set through command-line.

    :required:  True

``short``
    Short parameter form, used for e.g. ``-p value``.

    :required:  optional
    :type:      `str`

``long``
    Long parameter form, used for e.g. ``--parameter value``
    when it differs from its `name`.

    :required:  optional
    :type:      `str`

``type``
    Actually it can be any python callable.
    It coverts the string value received from command line to whatever
    value to be used on python code.

    If the ``type`` is ``bool`` the parameter is treated as an *option flag*
    where no value should be specified, value is set to ``True``.
    Example: ``doit mytask --flag``.

    :required:  optional
    :type:      `callable` (e.g. a `function`)
    :default:   `str`

``help``
    Help message associated to this parameter, shown when
    :ref:`help <cmd-help>` is called for this task,
    e.g. ``doit help mytask``.

    :required:  optional
    :type:      `str`

``inverse``
    [only for `bool` parameter]
    Set inverse flag long parameter name, value will be set to ``False``
    (see example below).

    :required:  optional
    :type:      `str`

    Example, given following code:

    .. literalinclude:: tutorial/parameters_inverse.py

    calls to task `with_flag` show flag on or off:

    .. code-block:: console

        $ doit with_flag
        .  with_flag
        Flag On
        $ doit with_flag --flagoff
        .  with_flag
        Flag Off


positional arguments
------------------------

Tasks might also get positional arguments from the command line
as standard unix commands do,
with positional arguments *after* optional arguments.

.. literalinclude:: tutorial/pos.py

.. code-block:: console

    $ doit pos_args -p 4 foo bar
    .  pos_args
    param1 is: 4
    positional-0: foo
    positional-1: bar


.. warning::

   If a task accepts positional arguments, it is not allowed to pass
   other tasks after it in the command line. For example if `task1`
   takes positional arguments you can not call::

     $ doit task1 pos1 task2

   As the string `task2` would be interpreted as positional argument from
   `task1` not as another task name.




.. _command line variables:

command line variables (*doit.get_var*)
-----------------------------------------

It is possible to pass variable values to be used in dodo.py from the command line.

.. literalinclude:: tutorial/get_var.py

.. code-block:: console

    $ doit
    .  echo
    hi {abc: NO}
    $ doit abc=xyz x=3
    .  echo
    hi {abc: xyz}



private/hidden tasks
---------------------

If task name starts with an underscore '_', it will not be included in the output.


title
-------

By default when you run `doit` only the task name is printed out on the output.
You can customize the output passing a "title" function to the task:

.. literalinclude:: tutorial/title.py

.. code-block:: console

    $ doit
    .  executing... Cmd: echo abc efg



.. _verbosity:


verbosity
-----------

By default the stdout from a task is captured and its stderr is sent to the
console. If the task fails or there is an error the stdout and a traceback
(if any) is displayed.

There are 3 levels of verbosity:

0:
  capture (do not print) stdout/stderr from task.

1 (default):
  capture stdout only.

2:
  do not capture anything (print everything immediately).


You can control the verbosity by:

* task attribute verbosity

.. literalinclude:: tutorial/verbosity.py

.. code-block:: console

    $ doit
    .  print
    hello

* from command line, see :ref:`verbosity option<verbosity_option>`.

.. _create-doit-tasks:


custom task definition
------------------------

Apart from collect functions that start with the name `task_`.
The *doit* loader will also execute the ``create_doit_tasks``
callable from any object that contains this attribute.


.. literalinclude:: tutorial/custom_task_def.py

The `project letsdoit <https://bitbucket.org/takluyver/letsdoit>`_
has some real-world implementations.

For simple examples to help you create your own check this
`blog post <http://blog.schettino72.net/posts/doit-task-creation.html>`_.


importing tasks
---------------

The *doit* loader will look at **all** objects in the namespace of the *dodo*.
It will look for functions staring with ``task_`` and objects with
``create_doit_tasks``.
So it is also possible to load task definitions from other
modules just by importing them into your *dodo* file.

.. literalinclude:: tutorial/import_tasks.py

.. code-block:: console

    $ doit list
    echo
    hello
    sample


.. note::

   Importing tasks from different modules is useful if you want to split
   your task definitions in different modules.

   The best way to create re-usable tasks that can be used in several projects
   is to call functions that return task dict's.
   For example take a look at a reusable *pyflakes*
   `task generator <https://github.com/pydoit/doit-py/blob/master/doitpy/pyflakes.py>`_.
   Check the project `doit-py <https://github.com/pydoit/doit-py>`_
   for more examples.
