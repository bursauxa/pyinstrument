pyinstrument backport to Python 2.4
===================================

[Pyinstrument](https://github.com/joerick/pyinstrument) is a Python profiler. A profiler is a tool to help you 'optimize'
your code - make it faster. It sounds obvious, but to get the biggest speed
increase you must [focus on the slowest part of your program](https://en.wikipedia.org/wiki/Amdahl%27s_law).
Pyinstrument helps you find it!

This fork is a backport of Pyinstrument to Python 2.4. It was forked from version 2.1.1 of Pyinstrument.
Please do not use it if you are running a version of Python that is natively supported by Pyinstrument (2.7 or 3.3+).

Installation
------------

Copy the `pyinstrument` folder to your library folder (i.e. somewhere in your PYTHONPATH).

How to use it
-------------

The only use case that was completely backported is the API that allows profiling a specific chunk of code.

```python
from pyinstrument import Profiler

profiler = Profiler()
profiler.start()

# code you want to profile

profiler.stop()

print(profiler.output_text(unicode=True, color=True))
```

(You can omit the `unicode` and `color` flags if your output/terminal does not support them.)

What is changed in this backport?
---------------------------------

### Breaking changes

- dropped support for the **pyinstrument C extension** because this fork can not use pip nor wheels.
  In practice it means: this version of the profiler has a larger performance overhead.
- dropped **dynamic imports**, which means that no custom renderers nor recorders can be used.

### Non-breaking changes

- added replacement code for **methodcaller** (part of the standard packages in 2.6+).
- added replacement code for **relpath** (part of the standard packages in 2.6+),
  not as good as the *real* relpath but it does the job in pyinstrument's case.
- enforced some path normalizations because there is no **os.fspath** to take care of it.
- rewrote **imports** in old style (no relative path shortcuts, mostly).
- rewrote **string formats** in old style (`%` instead of `format`).
- removed **six** and thus compatibility with Python 3, obviously.
- removed **abc** entirely, it was imported but not visibly used.
- replaced **with statements** with straigtforward open-close calls.
- replaced **ternary if-else assignations** with assignations behind multiple if statements.

### Unsupported scenarios

Neither the Django middleware nor the command-line `pyinstrument` were backported.
The files are still there, but they will not work if you try using them.

As a consequence, the HTML renderer was not tested.
However, all the code in `renderers.py` was backported, so the renderer itself *should* work.

This version was only tested on Linux (a CentOS as old as Python 2.4), but chances it works on Windows are high.

### Other

Items that will explicitly not be maintained as part of this backport have been removed from the repository. They are:

- examples, because all but one were Django-based, and the last one would require the command-line pyinstrument
- metrics, for many reasons: the c extension is not supported, cProfile is only for Python 2.5+, and Django is partially required
- tests, because pytest no longer supports anything before Python 2.7 and it actually breaks
- development, maintenance and setup files and documentation: this fork will never be published as a package