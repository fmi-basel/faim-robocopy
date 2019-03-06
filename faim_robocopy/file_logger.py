import os
import datetime
import logging


def _get_logfilename():
    '''constructs the logfile name.

    '''
    return 'Robocopy_Logfile_{}.html'.format(
        datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))


def _create_logfolder_if_necessary(basedir, subdir):
    '''create the folder basedir/subdir if it doesnt already exists.

    '''
    out_dir = os.path.join(basedir, subdir)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    return out_dir


def _get_logpath():
    '''constructs the logfile path.

    '''
    # Locations to check. high-priority first.
    potential_logdirs = [
        os.environ.get('USERPROFILE'),
        os.environ.get('HOMESHARE'),
        os.path.expanduser('~')
    ]
    potential_logdirs = [
        os.path.join(pot_dir, 'Desktop') for pot_dir in potential_logdirs
        if pot_dir is not None
    ]

    logfilename = _get_logfilename()

    # check locations to log to:
    for logdir in potential_logdirs:

        if os.path.exists(logdir):
            logdir = _create_logfolder_if_necessary(logdir,
                                                    'faim-robocopy-logs')
            return os.path.join(logdir, logfilename)

    raise IOError('Could not determine logfile path.')


def add_logging_to_file(filename):
    '''adds a FileHandler to the root logger.

    '''
    handler = logging.FileHandler(filename)
    formatter = logging.Formatter(
        '<p>%(asctime)s (%(name)s) [%(levelname)s]: %(message)s</p>',
        datefmt='%d.%m.%Y %H:%M:%S')
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
