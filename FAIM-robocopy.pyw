import argparse

import logging
import os

from faim_robocopy.starter import run_robocopy_gui

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] (%(name)s) [%(levelname)s]: %(message)s',
    datefmt='%d.%m.%Y %H:%M:%S')

def parse():
    '''parse command line arguments.

    '''
    parser = argparse.ArgumentParser('FAIM-Robocopy')
    parser.add_argument('--debug', help='enable debug log messages',
                        default=False, action='store_true')
    args = parser.parse_args()
    return vars(args)


def main():
    '''run FAIM-robocopy.
    
    Checks for latest version of FAIM-robocopy and updates/restarts if
    necessary.
    
    '''
    try:
        run_robocopy_gui(**parse())
    except Exception as err:
        logging.getLogger(__name__).error('Unexpected error: %s', str(err), exc_info=True)


if __name__ == '__main__':
    main()
