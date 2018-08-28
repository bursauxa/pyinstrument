import sys, os

from os.path import abspath, join, commonprefix

# replacement for os.path.relpath (2.6 and above)
# extracted from https://github.com/python/cpython/blob/master/Lib/posixpath.py
# several safety measures have been removed (os.fspath, better try-except statement, paths as bytes)
def relpath_unsafe(path, start=None):
    """Return a relative version of a path"""

    if not path:
        raise ValueError("no path specified")

    curdir = '.'
    sep = os.sep
    pardir = '..'

    if start is None:
        start = curdir

    try:
        start_list = [x for x in abspath(start).split(sep) if x]
        path_list = [x for x in abspath(path).split(sep) if x]
        # Work out how much of the filepath is shared by start and path.
        i = len(commonprefix([start_list, path_list]))

        rel_list = [pardir] * (len(start_list)-i) + path_list[i:]
        if not rel_list:
            return curdir
        return join(*rel_list)
    except (TypeError, AttributeError, BytesWarning, DeprecationWarning):
        raise

# replacement for operator.methodcaller (2.6 and above)
# equivalent definition provided by https://docs.python.org/3/library/operator.html#operator.methodcaller
def methodcaller(name, *args, **kwargs):
    def caller(obj):
        return getattr(obj, name)(*args, **kwargs)
    return caller

class Frame(object):
    """
    Object that represents a stack frame in the parsed tree
    """
    def __init__(self, identifier='', parent=None):
        self.identifier = identifier
        self.parent = parent
        self.self_time = 0

    @property
    def function(self):
        if self.identifier:
            return self.identifier.split('\x00')[0]

    @property
    def file_path(self):
        if self.identifier:
            return self.identifier.split('\x00')[1]

    @property
    def line_no(self):
        if self.identifier:
            return int(self.identifier.split('\x00')[2])

    @property
    def file_path_short(self):
        """ Return the path resolved against the closest entry in sys.path """
        if not hasattr(self, '_file_path_short'):
            if self.file_path:
                file_path_norm = os.path.normcase(os.path.normpath(self.file_path))
                result = None

                for path in sys.path:
                    # On Windows, if self.file_path and path are on different drives, relpath
                    # will result in exception, because it cannot compute a relpath in this case.
                    # The root cause is that on Windows, there is no root dir like '/' on Linux.
                    try:
                        candidate = relpath_unsafe(file_path_norm, os.path.normcase(os.path.normpath(path)))
                    except ValueError:
                        continue

                    if not result or (len(candidate.split(os.sep)) < len(result.split(os.sep))):
                        result = candidate

                self._file_path_short = result
            else:
                self._file_path_short = None

        return self._file_path_short

    @property
    def is_application_code(self):
        if self.identifier:
            return ('%slib%s' % (os.sep, os.sep)) not in self.file_path

    @property
    def code_position_short(self):
        if self.identifier:
            return '%s:%i' % (self.file_path_short, self.line_no)

    # stylistically I'd rather this was a property, but using @property appears to use twice
    # as many stack frames, so I'm forced into using a function since this method is recursive
    # down the call tree.
    def time(self):
        if not hasattr(self, '_time'):
            # can't use a sum(<generator>) expression here sadly, because this method
            # recurses down the call tree, and the generator uses an extra stack frame,
            # meaning we hit the stack limit when the profiled code is 500 frames deep.
            self._time = self.self_time

            for child in self._unsorted_children():
                self._time += child.time()

        return self._time

    @property
    def proportion_of_parent(self):
        if not hasattr(self, '_proportion_of_parent'):
            if self.parent and self.time():
                try:
                    self._proportion_of_parent = self.time() / self.parent.time()
                except ZeroDivisionError:
                    self._proportion_of_parent = float('nan')
            else:
                self._proportion_of_parent = 1.0

        return self._proportion_of_parent

    @property
    def proportion_of_total(self):
        if not hasattr(self, '_proportion_of_total'):
            if not self.parent:
                self._proportion_of_total = 1.0
            else:
                self._proportion_of_total = self.parent.proportion_of_total * self.proportion_of_parent

        return self._proportion_of_total

    def add_child(self, child):
        self.children.append(child)

    @property
    def children(self):
        raise NotImplementedError()

    # the ugly sibling of `children`, this method is only useful because it
    # doesn't recurse to return its value, to avoid "maximum recursion depth
    # exceeded" errors.
    def _unsorted_children(self):
        raise NotImplementedError()

    def __repr__(self):
        return 'Frame(identifier=%s, time=%f, len(children)=%d)' % (self.identifier, self.time(), len(self.children))


class TimelineFrame(Frame):
    def __init__(self, *args, **kwargs):
        self._children = []
        super(TimelineFrame, self).__init__(*args, **kwargs)

    def add_child(self, child):
        self._children.append(child)

    @property
    def children(self):
        return self._children

    def _unsorted_children(self):
        return self._children


class TimeAggregatingFrame(Frame):
    def __init__(self, *args, **kwargs):
        self.children_dict = {}
        super(TimeAggregatingFrame, self).__init__(*args, **kwargs)

    def add_child(self, child):
        self.children_dict[child.identifier] = child

    @property
    def children(self):
        if not hasattr(self, '_children'):
            self._children = sorted(self._unsorted_children(), key=methodcaller('time'), reverse=True)

        return self._children

    def _unsorted_children(self):
        return self.children_dict.values()
