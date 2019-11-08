import ctypes
import os
import socket
import re
import getpass
import logging
import filecmp
import functools
import time

from glob import glob
from fnmatch import fnmatch

# Root directory of project.
# E.g. used for updating via gitpython.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def count_files_in_subtree(folder, file_filter=None):
    '''count total number of files in folder and all subfolders.

    '''
    if file_filter is None:
        file_filter = _no_filter

    return sum([len(file_filter(files)) for _, _, files in os.walk(folder)])


def _sanitize_for_substitute(path):
    '''replaces backslashes in windows paths with / and
    converts Path objects to strings such that they can be used in
    re.sub routines.
 
    '''
    return str(path).replace('\\', '/')


def count_identical_files(source, destination, file_filter=None):
    '''counts identical files in two file trees.

    '''
    if file_filter is None:
        file_filter = _no_filter

    source = _sanitize_for_substitute(source)
    destination = _sanitize_for_substitute(destination)

    common_files = 0
    for current_dir, _, _ in os.walk(source):
        dest_dir = re.sub(source, destination, current_dir)

        if os.path.exists(dest_dir):

            # collect files that are in both folders
            potential_matches = file_filter(
                filecmp.dircmp(current_dir, dest_dir).common_files)

            # and compare them (shallow).
            (matches, _, _) = filecmp.cmpfiles(current_dir, dest_dir,
                                               potential_matches)
            common_files += len(matches)
    return common_files


def delete_files_older_than(folder, pattern, n_days):
    '''
    '''
    logger = logging.getLogger(__name__)
    logger.debug('Removing files matching %s older than %d days',
                 os.path.join(folder, pattern), n_days)

    now_in_seconds = time.time()
    limit_in_seconds = n_days * 24 * 3600

    counter = 0
    for path in glob(os.path.join(folder, pattern)):
        try:
            created_in_seconds = os.path.getctime(path)
            if now_in_seconds - created_in_seconds > limit_in_seconds:
                os.remove(path)
                counter += 1
        except OSError as err:
            logger.warning('Could not remove old file at %s: %s', path, err)

    logger.debug('Removed %d files', counter)


def is_filetree_a_subset_of(source, destination, file_filter=None):
    '''checks if destination contains a full copy of the filetree
    in source.

    '''
    if file_filter is None:
        file_filter = _no_filter

    source = _sanitize_for_substitute(source)
    destination = _sanitize_for_substitute(destination)

    assert os.path.exists(source)

    for current_source_dir, _, _ in os.walk(source):

        current_dest_dir = re.sub(source, destination, current_source_dir)

        if not os.path.exists(current_dest_dir):
            return False

        dir_cmp = filecmp.dircmp(current_source_dir, current_dest_dir)

        # are there some files in source only?
        if file_filter(dir_cmp.left_only):
            return False

        # are there some files that could not be compared?
        if file_filter(dir_cmp.funny_files):
            return False

        # dircmp only checks filenames, but we need at least a shallow
        # file comparison.
        (_, mismatches,
         errors) = filecmp.cmpfiles(current_source_dir, current_dest_dir,
                                    file_filter(dir_cmp.common_files))
        if mismatches or errors:
            return False

    return True


def _filter_dest(source, destinations):
    '''remove non-existing destinations and check for equality.

    '''
    logger = logging.getLogger(__name__)
    filtered_dest = []
    for dest in destinations:
        if os.path.realpath(dest) == os.path.realpath(source):
            logger.warning('Destination %s is equal to source directory %s!',
                           dest, source)
        elif not os.path.exists(dest):
            logger.warning('Destination %s doesnt exist!', dest)
        else:
            filtered_dest.append(dest)
    return filtered_dest


def delete_existing(source, destinations, file_filter=None):
    '''delete all files that were copied to all destinations.

    Parameters
    ----------
    source : path
        path to source folder.
    destinations : list of paths
        list of destination folders.

    '''
    logger = logging.getLogger(__name__)
    logger.info('Checking for fully copied source files for deletion...')

    if file_filter is None:
        file_filter = _no_filter

    # Sanitize destinations and make sure there is at least one.
    destinations = _filter_dest(source, destinations)

    if not destinations:
        raise RuntimeError('None of the given destinations was valid. '
                           'Do not delete any files.')

    source = _sanitize_for_substitute(source)
    destinations = [_sanitize_for_substitute(dest) for dest in destinations]

    assert os.path.exists(source)

    def _exists_in_all_destinations(path):
        '''
        '''
        path = _sanitize_for_substitute(path)
        try:
            return all((filecmp.cmp(path, re.sub(source, dest, path))
                        for dest in destinations))
        except FileNotFoundError:  # one of the files doesnt exist.
            return False
        except OSError:  # one of the files couldnt be accessed.
            return False

    # count the number of deleted files.
    n_deleted = 0

    # check for copied files in the entire file tree.
    for current_dir, _, files in os.walk(source):
        for filename in file_filter(files):
            filepath = os.path.join(current_dir, filename)

            # skip folders
            if os.path.isdir(filepath):
                continue

            try:
                if _exists_in_all_destinations(filepath):
                    try:
                        os.remove(filepath)
                        n_deleted += 1
                    except OSError as err:
                        logger.warning('Could not delete %s: %s', filepath,
                                       str(err))

            except Exception as err:
                logger.error(
                    'Problem with comparing/deleting file %s. Error: %s',
                    filename, str(err))

    # Deleting empty folders
    for current_dir, sub_dirs, files in os.walk(source, topdown=False):
        if not sub_dirs and not files and not current_dir == source:

            # only delete empty folders that exist in both destinations
            if all((os.path.exists(re.sub(source, dest, current_dir))
                    for dest in destinations)):
                os.rmdir(current_dir)

    logger.info('Deleted %d fully copied files from source.', n_deleted)

    return n_deleted


def create_file_filter(ignore_patterns):
    '''creates a file filter that removes files that match any
    of the given patterns.

    '''
    if ignore_patterns is not None or ignore_patterns == '':

        if isinstance(ignore_patterns, str):
            ignore_patterns = [
                ignore_patterns,
            ]

        return functools.partial(ignore_filter,
                                 ignore_patterns=ignore_patterns)

    logging.getLogger(__name__).debug(
        'Cannot create filter for the given patterns: %s', ignore_patterns)

    def _no_filter(file_list):
        return file_list

    return _no_filter


def ignore_filter(file_list, ignore_patterns):
    '''remove all files that match any of the given patterns.

    Parameters
    ----------
    file_list : list of paths
        list of paths to be filtered.
    ignore_patterns : list of str
        patterns matching files that are to be ignored. This supports
        all expressions that can be matched with ```fnmatch```.

    Returns
    -------
    filtered_files : list of paths
        filtered file list.

    '''
    return [
        item for item in file_list
        if not any(fnmatch(item, pat) for pat in ignore_patterns)
    ]


def _no_filter(file_list):
    '''
    '''
    return file_list


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


def get_hostname():
    '''return the local machine's hostname.

    '''
    return socket.gethostname()


def guess_user_mail(domain='fmi.ch'):
    '''construct user mail from display name.

    '''
    try:
        last, first = get_display_name().split(",")
        first = first[1:]  # TODO Why?
    except Exception:
        first, last = 'Firstname', 'Lastname'

    return '{first}.{last}@{domain}'.format(first=first,
                                            last=last,
                                            domain=domain)


def get_user_info():
    '''convenience function to construct a dict with user info.

    Return dict contains:
    - username
    - homeshare directory
    - user home directory
    - user mail (guess)

    '''
    return dict(username=get_username(),
                homeshare=get_homeshare(),
                user_dir=get_user_dir(),
                user_mail=guess_user_mail())
