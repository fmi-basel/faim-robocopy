import configparser
import logging
import os

from .utils import PROJECT_ROOT
from .utils import get_user_dir
from .utils import get_homeshare

DEFAULT_SETTINGS = os.path.join(PROJECT_ROOT, '.faimrobocopy_default.ini')

FNAME = '.faimrobocopy.ini'
CUSTOM_SETTINGS_PATHS = [
    os.path.join(get_user_dir(), FNAME),
    os.path.join(get_homeshare() if get_homeshare() is not None else '',
                 FNAME), DEFAULT_SETTINGS
]


class Settings(configparser.ConfigParser):
    '''
    '''

    def __init__(self):
        '''
        '''
        super().__init__()
        self.read_file(open(DEFAULT_SETTINGS, 'r'))

    def save(self, path):
        '''
        '''
        logging.getLogger(__name__).debug('Writing settings to %s', path)
        with open(path, 'w') as fout:
            self.write(fout)

    def get_mail_kwargs(self):
        '''
        '''
        return dict(self['email'])

    def get_robocopy_flags(self):
        '''
        '''
        try:
            return self['default_params']['custom_flags'].split(' ')
        except Exception:
            logging.getLogger(__name__).warning(
                'Could not parse custom flags for robocopy.')


def read_settings(path):
    '''
    '''
    settings = Settings()
    settings.read(path)
    return settings


def read_custom_settings():
    '''
    '''
    settings = Settings()
    for path in CUSTOM_SETTINGS_PATHS:

        success = settings.read(path)
        if success:
            return settings


def write_custom_settings(settings):
    '''
    '''
    outpath = CUSTOM_SETTINGS_PATHS[0]
    logging.getLogger(__name__).debug('Writing settings to %s', outpath)
    with open(outpath, 'w') as fout:
        settings.write(fout)
