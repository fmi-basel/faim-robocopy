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
    '''compare subdirectories. Returns True only if the subtrees are identical
    without considering files matching omitFile.

    '''
    # TODO Can we avoid this somehow?
    # TODO Refactor omitFile
    filecmp._filter = _filter

    dir_comparison = dircmp(source, destination, ignore=['*.' + omitFile])

    # are there some files that only occur in source?
    if len(dir_comparison.left_only) > 0:
        return False

    for racine, directories, _ in os.walk(source):
        for current_dir in directories:
            path1 = os.path.join(racine, current_dir)
            path2 = re.sub(source, destination, path1)

            if not os.path.exists(path2):
                # there is a subdir that doesnt exist in destination
                return False

            dir_comparison = dircmp(path1, path2, ignore=['*.' + omitFile])
            if len(dir_comparison.left_only) > 0:
                return False

    return True


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

    for racine, _, files in os.walk(source):
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
                logger.error('Problem with deleting files. Reason: %s',
                             str(err))
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
    username_ex = ctypes.windll.secur32.GetUserNameExW
    name_display = 3

    size = ctypes.pointer(ctypes.c_ulong(0))
    username_ex(name_display, None, size)
    name_buffer = ctypes.create_unicode_buffer(size.contents.value)
    username_ex(name_display, name_buffer, size)
    return name_buffer.value


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
    '''construct user mail from display name.

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