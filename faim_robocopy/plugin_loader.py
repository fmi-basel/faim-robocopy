import importlib
import logging
import os
from glob import glob

from tkinter import BooleanVar

from .utils import PROJECT_ROOT

PLUGIN_DIR = os.path.join(PROJECT_ROOT, 'plugins')

REQUESTED_ATTR = ['on_activation', 'on_task_end', 'description']
RESERVED_ATTR = ['_is_active_var']


def collect_plugins():
    '''
    '''

    def get_module_name(path):
        '''
        '''
        path = os.path.splitext(os.path.relpath(path, PLUGIN_DIR))[0]
        return '.' + path.replace(os.sep, '.')

    candidates = [
        get_module_name(path)
        for path in glob(os.path.join(PLUGIN_DIR, '*', 'plugin.py'))
    ]

    # import parent module / namespace
    importlib.import_module('plugins')
    plugins = {}

    for candidate in candidates:
        if candidate.startswith('__'):
            continue

        try:
            module = importlib.import_module(candidate, package='plugins')
        except Exception as err:
            logging.getLogger(__name__).debug(
                'Could not load plugin from %s. Reason: %s', candidate, err)
            continue

        for key, stuff in module.__dict__.items():
            if isinstance(stuff, type) and _check_if_plugin(stuff):
                plugins[key] = stuff

    if plugins:
        logging.getLogger(__name__).debug(
            'Loaded %d plugins: ' + ','.join(key for key in plugins.keys()),
            len(plugins))
    else:
        logging.getLogger(__name__).debug('Could not find any plugins')

    return plugins


def initialize_plugin(plugin_cls, *args, **kwargs):
    '''initalizes a collected plugin.

    '''
    logger = logging.getLogger(__name__)
    try:
        plugin = plugin_cls(*args, **kwargs)
        plugin._is_active_var = BooleanVar()
        logger.debug('Initialized plugin: %s', plugin_cls.__name__)
    except Exception as err:
        logger.error('Could not initialize plugin: %s', err)

    return plugin


def is_activated_plugin(plugin):
    '''
    '''
    return plugin._is_active_var.get()


def _check_if_plugin(cls):
    '''
    '''
    for method in REQUESTED_ATTR:
        if not hasattr(cls, method):
            return False
    for method in RESERVED_ATTR:
        if hasattr(cls, method):
            return False
    return True
