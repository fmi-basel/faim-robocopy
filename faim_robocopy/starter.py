import sys
import os
import logging

from tkinter import Tk

from faim_robocopy.gui import RobocopyGUI
from faim_robocopy.gui import get_window_name
from faim_robocopy.gui.updater import run_updater_ui

from faim_robocopy.file_logger import _get_logpath
from faim_robocopy.file_logger import add_logging_to_file


def run_robocopy_gui(debug):
    '''
    '''
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logfile = _get_logpath()
    add_logging_to_file(logfile)

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

    # Run updater at startup.
    run_updater_ui()

    # Start root
    root = Tk()
    root.title(get_window_name())
    RobocopyGUI(root, logfile)
    root.mainloop()
