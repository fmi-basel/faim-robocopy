import logging
import os

from threading import Thread
from tkinter import Tk

from .settings import read_custom_settings
from .auto_updater import run_updater_bg

from .gui import RobocopyGUI
from .gui import get_window_name
from .gui.updater import run_updater_ui

from .file_logger import _get_logpath
from .file_logger import add_logging_to_file
from .file_logger import LOGFILENAME_FMT

from .utils import delete_files_older_than


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

    # clean up old log files
    logger.info('Cleaning log folder')
    cleanup_thread = Thread(
        target=delete_files_older_than,
        kwargs=dict(folder=os.path.dirname(logfile),
                    pattern=LOGFILENAME_FMT.format('*'),
                    n_days=max(
                        settings['logging'].getfloat('clean_older_than_ndays'),
                        1.0)),
        daemon=True)
    cleanup_thread.start()

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
