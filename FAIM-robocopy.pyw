
import logging
import os

from faim_robocopy.starter import run_robocopy_gui

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] (%(name)s) [%(levelname)s]: %(message)s',
    datefmt='%d.%m.%Y %I:%M:%S')


def main():
    '''run FAIM-robocopy.
    
    Checks for latest version of FAIM-robocopy and updates/restarts if
    necessary.
    
    '''
    try:
        run_robocopy_gui()
    except Exception as err:
        logging.getLogger(__name__).error('Unexpected error: %s', str(err), exc_info=True)


if __name__ == '__main__':
    main()
