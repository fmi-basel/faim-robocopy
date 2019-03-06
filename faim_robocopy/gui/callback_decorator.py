from functools import wraps


class Context:
    '''Utility class to wrap a function with `with` such that
    enter and exit callbacks are called before and after, respectively.

    Example
    -------

    with Context(setup, cleanup):
        something()

    See also
    --------
    decorate_callback

    '''
    def __init__(self, enter_callback, exit_callback):
        '''
        '''
        self.enter_callback = enter_callback
        self.exit_callback = exit_callback

    def __enter__(self):
        '''
        '''
        self.enter_callback()

    def __exit__(self, *args, **kwargs):
        '''
        '''
        self.exit_callback()


def decorate_callback(func, enter_func, exit_func):
    '''runs runs enter_func before the call to func and exit_func after.

    Parameters
    ----------
    func : function
        function to be wrapped.
    enter_func : function
        function to be called before func.
    exit_func : function
        function to be called after func.

    Returns
    -------
    wrapped_func : function
        func decorated with Context(enter_func, exit_func).

    '''

    @wraps(func)
    def wrapped(*args, **kwargs):
        with Context(enter_func, exit_func):
            return func(*args, **kwargs)

    return wrapped
