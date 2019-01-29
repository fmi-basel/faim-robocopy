import sys
import os
import logging

from tkinter import Tk

from faim_robocopy.gui import RobocopyGUI
from faim_robocopy.auto_updater import auto_update_from_git
from faim_robocopy.auto_updater import restart
from faim_robocopy.auto_updater import UpdateExceptions
from faim_robocopy.utils import get_user_info
from faim_robocopy.file_logger import _get_logpath
from faim_robocopy.file_logger import add_logging_to_file


def run_robocopy_gui():
    '''
    '''
    logger = logging.getLogger(__name__)
    logger.info('Starting FAIM-robocopy')

    # Legacy code: redirect standard output streams
    # TODO Is this really needed?
    if sys.executable.endswith("pythonw.exe"):
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(
            os.path.join(
                os.getenv("TEMP"), "stderr-" + os.path.basename(sys.argv[0])),
            "w")

    # TODO consider opening a window that informs about update status.
    try:
        logfile = _get_logpath(get_user_info())
        add_logging_to_file(logfile)

        logger.info('Looking for updates...')
        needs_restart = auto_update_from_git(
            os.path.dirname(os.path.dirname(__file__)), 'origin', 'master')

        if needs_restart:
            logger.info('Updated. Restarting FAIM-robocopy...')
            restart()

        logger.info('Updater done.')

    except UpdateExceptions as err:
        print(err)
        logger.error('Auto-update failed: %s', str(err))
    except Exception as err:
        logger.error('Unexpected error during update: %s', str(err))

    # Start root
    root = Tk()
    root.title("Robocopy FAIM")
    RobocopyGUI(root, logfile)
    root.mainloop()
