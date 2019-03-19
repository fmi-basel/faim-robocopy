import logging

from tkinter import Tk

from .settings import read_custom_settings
from .auto_updater import run_updater_bg

from .gui import RobocopyGUI
from .gui import get_window_name
from .gui.updater import run_updater_ui

from .file_logger import _get_logpath
from .file_logger import add_logging_to_file


def run_robocopy_gui(debug):
    '''
    '''
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # load custom settings
    settings = read_custom_settings()

    # init logging
    logfile = _get_logpath()
    add_logging_to_file(logfile)

    logger = logging.getLogger(__name__)
    logger.info('Starting FAIM-robocopy')

    # Run updater at startup.
    if settings['updates'].getboolean('check_for_update_at_startup'):
        if settings['updates'].getboolean('show_window'):
            run_updater_ui()
        else:
            run_updater_bg()

    # Start root
    root = Tk()
    root.title(get_window_name())
    RobocopyGUI(root, logfile, settings)
    root.mainloop()
