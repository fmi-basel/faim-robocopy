
import logging
import os

from faim_robocopy.gui import run_robocopy_gui
from faim_robocopy.auto_updater import auto_update_from_git, restart, UpdateExceptions



logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] (%(name)s) [%(levelname)s]: %(message)s',
    datefmt='%d.%m.%Y %I:%M:%S')


def main():
    '''run FAIM-robocopy.
    
    Checks for latest version of FAIM-robocopy and updates/restarts if
    necessary.
    
    '''
    # TODO consider opening a window that informs about update status.
    try:
        logging.getLogger(__name__).info('Looking for updates...')
        needs_restart = auto_update_from_git(
            os.path.dirname(__file__), 'origin', 'master')
        if needs_restart:
            logging.getLogger(__name__).info('Updated. Restarting FAIM-robocopy...')
            restart()
    except UpdateExceptions as err:
        logging.getLogger(__name__).error('Auto-update failed: %s', str(err))
    except Exception as err:
        logging.getLogger(__name__).error('Unexpected error: %s', str(err))

    try:
        run_robocopy_gui()
    except Exception as err:
        logging.getLogger(__name__).error('Unexpected error: %s', str(err), exc_info=True)


if __name__ == '__main__':
    main()
