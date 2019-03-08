import ctypes
import os
import re
import getpass
import logging
import filecmp
from filecmp import dircmp
from fnmatch import fnmatch

# Root directory of project.
# E.g. used for updating via gitpython.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def count_files_in_subtree(folder):
    '''count total number of files in folder and all subfolders.

    '''
    return sum([len(files) for _, _, files in os.walk(folder)])


def count_identical_files(source, destination, omit_files):
    '''counts identical files in two file trees.

    '''
    # TODO Refactor
    filecmp._filter = _filter

    common_files = 0
    for current_dir, _, _ in os.walk(source):
        dest_dir = re.sub(source, destination, current_dir)

        if os.path.exists(dest_dir):
            comparison = dircmp(
                current_dir, dest_dir, ignore=['*.' + omit_files])
            (matches, _, _) = filecmp.cmpfiles(current_dir,
                                               dest_dir,
                                               comparison.common_files)
            common_files += len(matches)
    return common_files


def is_filetree_a_subset_of(source, destination, skip_files=None):
    '''checks if destination contains a full copy of the filetree
    in source.

    '''
    if not isinstance(skip_files, list) or skip_files is None:
        skip_files = list(skip_files)

    for current_source_dir, _, source_filenames in os.walk(source):

        current_dest_dir = re.sub(source, destination, current_source_dir)

        if not os.path.exists(current_dest_dir):
            return False

        dir_cmp = filecmp.dircmp(
            current_source_dir, current_dest_dir, ignore=skip_files)

        if dir_cmp.left_only:  # there are some files in source only.
            return False

        # there are some files that could not be compared.
        if dir_cmp.funny_files:
            return False

        # dircmp only checks filenames, but we need at least a shallow
        # file comparison.
        (_, mismatches, errors) = filecmp.cmpfiles(
            current_source_dir, current_dest_dir, dir_cmp.common_files)
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


def delete_existing(source, destinations):
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

    # Sanitize destinations and make sure there is at least one.
    destinations = _filter_dest(source, destinations)

    if not destinations:
        raise RuntimeError('None of the given destinations was valid. '
                           'Do not delete any files.')

    def _exists_in_all_destinations(path):
        '''
        '''
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
        for filename in files:
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
        first, last = 'Firstname', 'Lastname'

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
