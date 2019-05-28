import logging
import subprocess
import os
import datetime
import time
import re

from concurrent.futures import ThreadPoolExecutor
from collections import namedtuple

from faim_robocopy.utils import is_filetree_a_subset_of
from faim_robocopy.utils import delete_existing
from faim_robocopy.utils import count_files_in_subtree
from faim_robocopy.utils import count_identical_files
from faim_robocopy.utils import create_file_filter


def _sanitize_destinations(destinations):
    '''
    '''
    # check number of dest
    if not isinstance(destinations, (tuple, list)):
        destinations = [destinations]

    # warn user if a destination doesnt exist...
    for dest in destinations:
        if dest == '':
            pass
        elif not os.path.isdir(dest):
            logging.getLogger(__name__).warning(
                'Destination %s does not exist!', dest)

    # ...and clean it up
    return [
        dest for dest in destinations if dest != '' and os.path.exists(dest)
    ]


def _sanitize_ignore_patterns(ignore_patterns, delimiter=';'):
    '''turns a string of ignore patterns into a list of patterns.

    Notes
    -----
    Leading or trailing whitespace is removed.

    '''
    if isinstance(ignore_patterns, str):
        ignore_patterns = ignore_patterns.split(delimiter)

    ignore_patterns = [pat.strip(' ') for pat in ignore_patterns]
    logging.getLogger(__name__).debug(
        'Ignoring all files that match any of the following patterns: %s',
        ignore_patterns)

    return ignore_patterns


def _report(source, destinations, file_filter, n_deleted):
    '''report the number of present and identical files in source and
    destination folders.

    '''
    logger = logging.getLogger(__name__)

    for folder in [
            source,
    ] + destinations:

        if folder == '':
            continue

        try:
            filecount = count_files_in_subtree(folder, file_filter=file_filter)

            if folder != source:
                identical = count_identical_files(source, folder, file_filter)
                logger.info('%d files (total) in %s, %d identical to source',
                            filecount, folder, identical)
            else:
                logger.info('%d files (total) in %s', filecount, folder)
                if n_deleted > 0:
                    logger.info('%d files were deleted from %s', n_deleted,
                                folder)

        except Exception as err:
            logger.error('Could not count files in %s. Error: %s', folder,
                         str(err))


class RobocopyTask:
    '''Watches a source folder and launches robocopy calls for new data.
    Provides a terminate functionality to abort running threads preliminarily.

    '''

    def __init__(self, notifier, additional_flags=None):
        '''
        '''
        self._running = False
        self.futures = {}
        self._update_rate_in_s = 5.
        self._time_at_last_change = datetime.datetime.now()
        self.notifier = notifier
        self.additional_flags = additional_flags

    def terminate(self):
        '''requests the task to terminate.

        '''
        if self.is_running():
            logging.getLogger(__name__).warning('Stopping robocopy task')

        # prevent queued jobs from starting after terminate was called.
        for future in self.futures.values():
            future.cancel()

        self._running = False

    def _update_changed(self):
        '''
        '''
        self._time_at_last_change = datetime.datetime.now()

    def _wait_has_expired(self, time_to_exit_in_s):
        '''
        '''
        time_since_update = (datetime.datetime.now() -
                             self._time_at_last_change).total_seconds()
        logging.getLogger(__name__).debug(
            'Time since last detected change: %1.1f s',
            float(time_since_update))
        return time_since_update >= time_to_exit_in_s

    def is_running(self):
        '''
        '''
        return self._running

    def __enter__(self):
        '''
        '''
        logging.getLogger(__name__).info('Starting robocopy task')
        self._running = True

    def __exit__(self, *args, **kwargs):
        '''
        '''
        self._running = False

    def run(self, *args, **kwargs):
        '''runs the robocopy task.

        '''
        with self:
            return self._run(*args, **kwargs)

    def _run(self, source, destinations, multithread, time_interval, wait_exit,
             delete_source, exclude_files, **robocopy_kwargs):
        '''actual robocopy task function. Call the public method to ensure that the
        is_running() state is properly set on entering and exiting.

        '''
        # Log start
        logger = logging.getLogger(__name__)

        # sanitize destinations
        destinations = _sanitize_destinations(destinations)

        # sanitize ignore_patterns and turn them into a filter.
        exclude_files = _sanitize_ignore_patterns(exclude_files)
        file_filter = create_file_filter(exclude_files)

        if not destinations:
            raise RuntimeError('Need at least one destination to copy to.')

        logging.getLogger(__name__).info('Source folder: %s', source)
        for counter, dest in enumerate(destinations):
            logging.getLogger(__name__).info('Destination folder %d: %s',
                                             counter + 1, dest)

        # Define the number of threads for copying
        max_workers = 2 if (multithread and len(destinations) >= 2) else 1
        n_deleted = 0

        def _robocopy_callback(future):
            '''handles the logging of robocopy jobs and sends a mail in case of
                failure.

                '''
            if future.cancelled():
                logger.debug('Robocopy job cancelled')
            elif future.done():
                error = future.exception()
                if error:
                    # NOTE unfortunately, we dont know which destination
                    # the failing job had but we can report the error.
                    if isinstance(error, RobocopyError):
                        logger.error('%s', error)
                    else:
                        logger.error('Robocopy failed with error %s', error)
                    self.notifier.failed(error)
                else:
                    logger.debug('Robocopy job terminated successfully')

        def _submit(destination):
            '''submits tasks for execution in thread_pool and returns its future.

            '''
            # NOTE thread_pool is resolved at call time.
            future = thread_pool.submit(robocopy_call,
                                        source=source,
                                        dest=dest,
                                        exclude_files=exclude_files,
                                        additional_flags=self.additional_flags,
                                        **robocopy_kwargs)
            future.add_done_callback(_robocopy_callback)
            return future

        with ThreadPoolExecutor(max_workers=max_workers) as thread_pool:

            self._update_changed()

            # Make at least one robocopy call for each directory
            # even if we dont have anything to do yet.
            self.futures = {dest: _submit(dest) for dest in destinations}

            # Monitor source and dest folders and start robocopy jobs
            # whenever a source and destination have different content.
            while self.is_running():

                # prevent an early stop when the robocopy job is running long.
                if any(future.running() for future in self.futures.values()):
                    self._update_changed()

                # Terminate if wait_exit is expired without any new
                # file to copy.
                if self._wait_has_expired(wait_exit * 60.):
                    logger.info('Stopping robocopy after %1.1f min of waiting',
                                wait_exit)
                    break

                # For all those futures that are finished, we check if
                # there are new files.
                for dest in destinations:

                    if not is_filetree_a_subset_of(source, dest, file_filter):
                        self._update_changed()

                        if self.futures[dest].done():
                            self.futures[dest] = _submit(dest)

                # delete files that are copied to all destinations.
                if delete_source:
                    n_deleted += delete_existing(source, destinations,
                                                 file_filter)

                # wait
                if any(future.running() for future in self.futures.values()):
                    logger.info('Robocopy jobs running...')
                else:
                    logger.info(
                        'Waiting for %1.1f min before checking for new files to copy',
                        float(time_interval))

                # Sleep with polling for a potential terminate() signal
                for _ in range(
                        int(time_interval * 60. / self._update_rate_in_s)):
                    time.sleep(self._update_rate_in_s)
                    if not self.is_running():
                        break

        # Report files in both folders.
        logger.info('Robocopy summary:')
        _report(source, destinations, file_filter, n_deleted)

        # Notify user about success.
        self.notifier.finished(source, destinations)


def build_robocopy_command(source, dest, exclude_files, additional_flags):
    '''builds the robocopy call command.

    '''
    # Robocopy syntax:
    # robocopy <Source> <Destination> [<File>[ ...]] [<Options>]
    # - /XF: exclude files
    # - /e:  copy subdirectories
    #
    # https://docs.microsoft.com/en-us/windows-server/administration/windows-commands/robocopy
    cmd = ['robocopy', source, dest, "/e", "/COPY:DT"]

    if exclude_files is not None and not exclude_files == '':
        cmd.extend([
            '/XF',
        ] + exclude_files)

    # previously known as "secure mode"
    cmd.extend(["/r:1", "/w:30", "/dcopy:T", "/Z"])

    # remove job header and summary from log, but be verbose about files.
    cmd.extend(['/V', '/njh', '/njs'])

    # additional flags.
    if additional_flags is not None:
        cmd.extend(additional_flags)

    return cmd


def robocopy_call(source, dest, exclude_files=None, additional_flags=None):
    '''run an individual robocopy call.

    Parameters
    ----------
    source : path
        source folder.
    dest : path
        destination folder.
    exclude_files : list of strings
        files or file patterns to be ignored.
    additional_flags : list of strings
        additional robocopy flags to be passed "as-is". Use carefully.

    Notes
    -----
    An error is raised if Robocopy returns with an exit code >= 8.

    '''
    cmd = build_robocopy_command(source, dest, exclude_files, additional_flags)

    call_kwargs = dict()

    try:
        logging.getLogger(__name__).debug(cmd)
        subprocess.check_output(cmd, **call_kwargs)
    except subprocess.CalledProcessError as err:
        exit_code = err.returncode
        logging.getLogger(__name__).debug('Robocopy nonzero exit code: %s',
                                          exit_code)

        # Return codes above 8 are errors
        if exit_code >= 8:
            raise RobocopyError.from_error(err) from err
        elif 2 <= exit_code < 8:
            logging.getLogger(__name__).debug(
                'Robocopy exited with code %d. This is not a failure.',
                exit_code)


class RobocopyError(Exception):
    '''Robocopy exception for return codes >= 8.

    '''

    def __init__(self, returncode, error_info):
        '''
        '''
        super().__init__()
        self.returncode = returncode
        self.error_info = error_info

    @classmethod
    def from_error(cls, called_subprocess_error):
        '''create a RobocopyError from a CalledProcessError.

        '''
        return cls(returncode=called_subprocess_error.returncode,
                   error_info=parse_errors_from_robocopy_stdout(
                       called_subprocess_error.output))

    def __str__(self):
        '''format error message.

        '''
        msg = 'Robocopy returned with exit code %s.' % self.returncode
        if not self.error_info or self.error_info is None:

            msg += ' No detailled information available.'
            return msg

        msg += ' The following issues were encountered:\n'
        for code, action, reason in self.error_info:
            msg += '  [Code %s] %s: %s\n' % (code, action, reason)
        return msg


def parse_errors_from_robocopy_stdout(output):
    '''parse error information from output of a single robocopy run.

    '''
    output = output.decode('UTF-8')
    logger = logging.getLogger(__name__ + '.parser')
    RobocopyErrorInfo = namedtuple('RobocopyErrorInfo',
                                   ['code', 'action', 'reason'])

    pattern = re.compile(r'ERROR\s+(\d+)\s+\(0x[0-9a-fA-F]+\)\s+(.*)\n^(.*)$',
                         re.MULTILINE)

    matches = re.findall(pattern, output)
    if matches:
        return [
            RobocopyErrorInfo(*[val.strip('\r') for val in match])
            for match in matches
        ]

    # try to get a more general error message
    pattern = re.compile(r'ERROR\s+:\s+(.*)$', re.MULTILINE)
    matches = re.findall(pattern, output)
    if matches:
        return [
            RobocopyErrorInfo(-1, '', match.strip('\r')) for match in matches
        ]

    logger.debug('Could not parse any errors from stdout of robocopy')
    logger.debug('Raw robocopy stdout:\n %s', output)
    return [
        RobocopyErrorInfo(
            -1, '', 'Could not parse any errors from stdout of robocopy')
    ]
