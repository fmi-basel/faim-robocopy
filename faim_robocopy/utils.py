import ctypes
import os
import re
import getpass
import logging

import filecmp
from filecmp import dircmp
from fnmatch import fnmatch


def count_files_in_subtree(folder):
    '''count total number of files in folder and all subfolders.

    '''
    return sum([len(files) for _, _, files in os.walk(folder)])


def compsubfolders(source, destination, omitFile):
    '''compare subdirectories.

    '''
    # TODO Can we avoid this somehow?
    filecmp._filter = _filter

    # TODO Refactor omitFile
    # TODO We dont necessarily need to traverse
    # all subfolders if we just want to say if the two folders are
    # different.
    condition = True
    myComp = dircmp(source, destination, ignore=['*.' + omitFile])
    if len(myComp.left_only) != 0:
        condition = False
    for racine, directories, files in os.walk(source):
        for myDir in directories:
            path1 = os.path.join(racine, myDir)
            path2 = re.sub(source, destination, path1)
            if os.path.exists(path2):
                myComp = dircmp(path1, path2, ignore=['*.' + omitFile])
                if len(myComp.left_only) != 0:
                    condition = False
            else:
                condition = False
    return condition


def delete_existing(source, destinations):
    '''delete all files that were copied to all destinations.

    '''
    logger = logging.getLogger(__name__)
    logger.info('Deleting source files that have been fully copied')

    # make sure there is at least one destination.
    def _filter_dest(source, destinations):
        '''remove non-existing destinations and check for equality.

        '''
        filtered_dest = []
        for dest in destinations:
            if os.path.realpath(dest) == os.path.realpath(source):
                logger.warning(
                    'Destination %s is equal to source directory %s!', dest,
                    source)
            elif not os.path.exists(dest):
                logger.warning('Destination %s doesnt exist!', dest)
            else:
                filtered_dest.append(dest)
        return filtered_dest

    destinations = _filter_dest(source, destinations)
    if len(destinations) == 0:
        raise RuntimeError('None of the given destinations was valid. '
                           'Do not delete any files.')

    def _exists_in_all_destinations(path):
        '''
        '''
        # TODO should this be a deep comparison?
        try:
            return all((filecmp.cmp(path, re.sub(source, dest, path))
                        for dest in destinations))
        except FileNotFoundError:
            return False

    for racine, directories, files in os.walk(source):
        for filename in files:
            filepath = os.path.join(racine, filename)

            # skip folders
            if os.path.isdir(filepath):
                continue

            try:
                if _exists_in_all_destinations(filepath):
                    try:
                        os.remove(filepath)
                    except Exception as err:
                        logger.error('Could not delete %s yet. Reason: %s',
                                     filepath, str(err))

            # Legacy catches. TODO Do we need all of these?
            except OSError as err:
                logger.error(
                    'Problem with deleting files. Reason: %s', str(err))
            except ValueError as err:
                logger.error(
                    'Problem with deleting files. Could not convert data to an integer.'
                )
            except Exception as err:
                logger.error(
                    'Problem with deleting files. Unexpected error: %s',
                    str(err))
                raise

    # Deleting empty folders
    for current_dir, sub_dirs, files in os.walk(source, topdown=False):
        if len(sub_dirs) + len(files) == 0 and not current_dir == source:
            os.rmdir(current_dir)


# TODO Refactor naming
# TODO Try to get rid of this
def _filter(file_list, skip_patterns):
    '''remove all files that match any of the given patterns.

    '''
    return [
        item for item in file_list
        if not any(fnmatch(item, pat) for pat in skip_patterns)
    ]


def get_display_name():
    '''get user full name.

    NOTE: Relies on ctypes.windll and is thus only
    functional on windows.

    '''
    GetUserNameEx = ctypes.windll.secur32.GetUserNameExW
    NameDisplay = 3

    size = ctypes.pointer(ctypes.c_ulong(0))
    GetUserNameEx(NameDisplay, None, size)
    nameBuffer = ctypes.create_unicode_buffer(size.contents.value)
    GetUserNameEx(NameDisplay, nameBuffer, size)
    return nameBuffer.value


def get_username():
    '''return system username.

    '''
    return getpass.getuser()


def get_homeshare():
    '''Path to home share. Returns None in case the environment
    variable is undefined.

    '''
    return os.environ.get('HOMESHARE', None)


def get_user_dir():
    '''return the users home directory.

    '''
    return os.path.expanduser('~')


def guess_user_mail(domain='fmi.ch'):
    '''
    '''
    try:
        last, first = get_display_name().split(",")
        first = first[1:]  # TODO Why?
    except Exception:
        last, first = 'Firstname', 'LastName'

    return '{first}.{last}@{domain}'.format(
        first=first, last=last, domain=domain)


def get_user_info():
    '''convenience function to construct a dict with user info.

    Return dict contains:
    - username
    - homeshare directory
    - user home directory
    - user mail (guess)

    '''
    return dict(
        username=get_username(),
        homeshare=get_homeshare(),
        user_dir=get_user_dir(),
        user_mail=guess_user_mail())
