import logging
import sys
import os

from git import Repo
from git import InvalidGitRepositoryError
from git import GitCommandError

# Grab working directory at import for restart().
# NOTE This relies on an early import in order to work as expected.
# NOTE (Technique from the cherrypy project)
_STARTUP_CWD = os.getcwd()


# Exceptions raised by auto_update
UpdateExceptions = (InvalidGitRepositoryError, GitCommandError)


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
    logging.getLogger(__name__).debug('Active branch: %s', branch)

    if branch is None:
        branch = active_branch

    if branch != active_branch:
        logging.getLogger(__name__).warning(
            'Branch to update from (%s) is not the branch that is currently active (%s)!',
            branch, active_branch)

    # Pull. This raises if anything goes wrong.
    logging.getLogger(__name__).debug('Pull branch %s from %s', branch, remote)
    retval = repo.git.pull(remote, branch)
    logging.getLogger(__name__).debug(retval)

    if 'Already up to date.' in retval:
        return False

    return True


def restart():
    '''restarts the current process and terminates.

    '''
    args = sys.argv[:]
    logging.getLogger(__name__).info('Re-spawning %s' % ' '.join(args))

    args.insert(0, sys.executable)
    if sys.platform == 'win32':
        args = ['"%s"' % arg for arg in args]

    os.chdir(_STARTUP_CWD)
    os.execv(sys.executable, args)
    exit()
