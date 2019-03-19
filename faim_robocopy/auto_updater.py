import logging
import sys
import os
import re

from git import Repo
from git import InvalidGitRepositoryError
from git import GitCommandError

# Grab working directory at import for restart().
# NOTE This relies on an early import in order to work as expected.
# NOTE (Technique from the cherrypy project)
_STARTUP_CWD = os.getcwd()


# Error raised by auto_update_from_git if the return of git pull
# could not be associated with success or failure.
class UnknownPullReturnCodeError(Exception):
    pass


# Exceptions raised by auto_update
UpdateExceptions = (InvalidGitRepositoryError, GitCommandError,
                    UnknownPullReturnCodeError)

# Silence gitpython's logger
logging.getLogger('git').setLevel(logging.ERROR)
logging.getLogger('git.cmd').setLevel(logging.ERROR)


def auto_update_from_git(repo_path, remote='origin', branch=None):
    '''updates code by pulling the latest version from the remote
    git repository.

    Parameters
    ----------
    repo_path : path
        path to local repository.
    remote : string
        name of remote repo. Default: origin
    branch : string
        name of branch. Default: currently active branch

    Returns
    -------
    updated : bool
        True if the code was updated, False otherwise.

    '''
    # will raise git.InvalidGitRepository if there is no git repo in path.
    repo = Repo(repo_path)

    active_branch = repo.active_branch.name
    logging.getLogger(__name__).debug('Active branch: %s', active_branch)

    if branch is None:
        branch = active_branch

    if branch != active_branch:
        logging.getLogger(__name__).warning(
            'Branch to update from (%s) is not the branch that is currently active (%s)!',
            branch, active_branch)

    # git pull. This raises if anything goes wrong.
    logging.getLogger(__name__).debug('Pull branch %s from %s', branch, remote)
    retval = repo.git.pull(remote, branch)
    logging.getLogger(__name__).debug(retval)

    if re.search('Already.up.to.date', retval):
        return False
    if re.search('Updating', retval) and (re.search('file.changed', retval) or
                                          re.search('files.changed', retval)):
        return True
    raise UnknownPullReturnCodeError('git pull returned {}'.format(retval))


def restart():
    '''restarts the current process and terminates.

    '''
    args = sys.argv[:]
    logging.getLogger(__name__).info('Re-spawning %s' % ' '.join(args))

    # make sure all loggers release their file handles
    logging.shutdown()

    args.insert(0, sys.executable)
    if sys.platform == 'win32':
        args = ['"%s"' % arg for arg in args]

    os.chdir(_STARTUP_CWD)
    os.execv(sys.executable, args)
    exit()


def run_updater_bg():
    '''try to update and restart if necessary. Progress will be logged,
    but no user interface will be presented.

    '''
    logger = logging.getLogger(__name__)
    try:
        logger.info('Looking for updates...')
        needs_restart = auto_update_from_git(
            os.path.dirname(os.path.dirname(__file__)), 'origin', 'master')

        if needs_restart:
            logger.info('Updated. Restarting FAIM-robocopy...')
            restart()

        logger.info('Updater done.')

    except UpdateExceptions as err:
        logger.error('Auto-update failed: %s', str(err))
    except Exception as err:
        logger.error('Unexpected error during update: %s', str(err))
