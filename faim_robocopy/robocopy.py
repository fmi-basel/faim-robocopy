import logging
import subprocess
import os
import datetime
import time
import re
import psutil

from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from collections import namedtuple
from threading import Lock

from faim_robocopy.utils import is_filetree_a_subset_of
from faim_robocopy.utils import delete_existing
from faim_robocopy.utils import count_files_in_subtree
from faim_robocopy.utils import count_identical_files
from faim_robocopy.file_filter import create_file_filter


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


def _sanitize_patterns(patterns, delimiter=';'):
    '''turns a string of exclude/include patterns into a list of patterns.

    Notes
    -----
    Leading or trailing whitespace is removed.

    '''
    if isinstance(patterns, str):
        patterns = patterns.split(delimiter)

    patterns = [
        pat for pat in (pat.strip(' ') for pat in patterns) if pat != ''
    ]

    logging.getLogger(__name__).debug('Sanitized the following patterns: %s',
                                      patterns)
    return patterns


def _report(source, destinations, file_filter, n_deleted):
    '''report the number of present and identical files in source and
    destination folders.

    '''
    logger = logging.getLogger(__name__)

    # collect statistics on files/folders
    FolderStat = namedtuple('folder_stat',
                            ['folder', 'filecount', 'identical'])
    stats = []

    for folder in [
            source,
    ] + destinations:

        if folder == '':
            continue

        try:
            filecount = count_files_in_subtree(folder, file_filter=file_filter)

            if folder != source:
                identical = count_identical_files(source, folder, file_filter)
            else:
                identical = None

            stats.append(FolderStat(folder, filecount, identical))

        except Exception as err:
            logger.error('Could not count files in %s. Error: %s', folder,
                         str(err))

    # write stats to log.
    for stat in stats:
        if stat.identical is not None:
            logger.info('%d files (total) in %s, %d identical to source',
                        stat.filecount, stat.folder, stat.identical)
        else:
            logger.info('%d files (total) in %s', stat.filecount, stat.folder)
            if n_deleted > 0:
                logger.info('%d files were deleted from %s', n_deleted,
                            stat.folder)


class SubprocessLauncher:
    def __init__(self):
        self._registered_processes = []
        self._lock = Lock()

    def _register(self, process):
        with self._lock:
            self._registered_processes.append(process.pid)

    def _deregister(self, process):
        with self._lock:
            self._registered_processes.remove(process.pid)

    @contextmanager
    def track(self, process):
        self._register(process)
        try:
            yield
        finally:
            self._deregister(process)

    def check_output(self, *popenargs, timeout=None, **kwargs):
        if 'stdout' in kwargs:
            raise ValueError(
                'stdout argument not allowed, it will be overridden.')

        if 'input' in kwargs and kwargs['input'] is None:
            # Explicitly passing input=None was previously equivalent to passing an
            # empty string. That is maintained here for backwards compatibility.
            kwargs['input'] = '' if kwargs.get('universal_newlines',
                                               False) else b''
        return self.run(*popenargs,
                        stdout=subprocess.PIPE,
                        timeout=timeout,
                        check=True,
                        **kwargs).stdout

    def run(self,
            *popenargs,
            input=None,
            capture_output=False,
            timeout=None,
            check=False,
            **kwargs):
        if input is not None:
            if kwargs.get('stdin') is not None:
                raise ValueError(
                    'stdin and input arguments may not both be used.')
            kwargs['stdin'] = subprocess.PIPE

        if capture_output:
            if kwargs.get('stdout') is not None or kwargs.get(
                    'stderr') is not None:
                raise ValueError('stdout and stderr arguments may not be used '
                                 'with capture_output.')
            kwargs['stdout'] = subprocess.PIPE
            kwargs['stderr'] = subprocess.PIPE

        with subprocess.Popen(*popenargs, **kwargs) as process:
            with self.track(process):
                try:
                    stdout, stderr = process.communicate(input,
                                                         timeout=timeout)
                except TimeoutExpired as exc:
                    process.kill()
                    exc.stdout, exc.stderr = process.communicate()
                    raise
                except:  # Including KeyboardInterrupt, communicate handled that.
                    process.kill()
                    # We don't call process.wait() as .__exit__ does that for us.
                    raise
                retcode = process.poll()
                if check and retcode:
                    raise subprocess.CalledProcessError(retcode,
                                                        process.args,
                                                        output=stdout,
                                                        stderr=stderr)

            return subprocess.CompletedProcess(process.args, retcode, stdout,
                                               stderr)

    def terminate(self):
        with self._lock:
            for pid in self._registered_processes:
                try:
                    psutil.Process(pid).terminate()
                except Exception as err:
                    logging.getLogger(__name__).error(
                        'Could not terminate process with pid: %s', err)


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
        self.subprocess_launcher = SubprocessLauncher()

    def terminate(self):
        '''requests the task to terminate.

        '''
        if not self.is_running():
            logging.getLogger(__name__).warning(
                'RobocopyTask is already stopped or in the process of stopping.'
            )
            return

        logging.getLogger(__name__).warning('Stopping robocopy task')
        self._running = False

        # prevent queued jobs from starting after terminate was called.
        for future in self.futures.values():
            future.cancel()

        # kill any running robocopy processes.
        self.subprocess_launcher.terminate()

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
             delete_source, exclude_files, include_files, **robocopy_kwargs):
        '''actual robocopy task function. Call the public method to ensure that the
        is_running() state is properly set on entering and exiting.

        '''
        # Log start
        logger = logging.getLogger(__name__)

        # sanitize destinations
        destinations = _sanitize_destinations(destinations)

        # sanitize ignore_patterns and turn them into a filter.
        exclude_files = _sanitize_patterns(exclude_files)
        include_files = _sanitize_patterns(include_files)
        file_filter = create_file_filter(ignore_patterns=exclude_files,
                                         include_patterns=include_files)

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
            future = thread_pool.submit(self.robocopy_call,
                                        source=source,
                                        dest=destination,
                                        exclude_files=exclude_files,
                                        include_files=include_files,
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

                # delete files that are copied to all destinations.
                if delete_source:
                    n_deleted += delete_existing(source, destinations,
                                                 file_filter)

                for dest in destinations:
                    # prevent an early stop when the robocopy job is running long.
                    if self.futures[dest].running():
                        self._update_changed()
                        logger.info('Robocopy jobs running...')

                    # For all those futures that are finished, we check if
                    # there are new files.
                    elif self.futures[dest].done():
                        if not is_filetree_a_subset_of(source, dest,
                                                       file_filter):
                            self._update_changed()
                            self.futures[dest] = _submit(dest)
                            logger.info(
                                'Found new files in source. Starting a new robocopy job...'
                            )
                        else:
                            logger.info(
                                'Waiting for %1.1f min before checking for new files to copy',
                                float(time_interval))

                # Terminate if wait_exit is expired without any new
                # file to copy.
                if self._wait_has_expired(wait_exit * 60.):
                    logger.info('Stopping robocopy after %1.1f min of waiting',
                                wait_exit)
                    break

                # Sleep with polling for a potential terminate() signal
                for _ in range(
                        int(time_interval * 60. / self._update_rate_in_s)):
                    time.sleep(self._update_rate_in_s)
                    if not self.is_running():
                        break

        # Report files in both folders.
        logger.warn('Collecting summary of previous robocopy run... '
                    '(this may take up to a few minutes if there are '
                    'a thousands of files in source/destination)')
        _report(source, destinations, file_filter, n_deleted)
        logger.info('Summary done.')

        # Notify user about success.
        self.notifier.finished(source, destinations)

    def robocopy_call(self,
                      source,
                      dest,
                      exclude_files=None,
                      include_files=None,
                      additional_flags=None):
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
        cmd = build_robocopy_command(source,
                                     dest,
                                     exclude_files=exclude_files,
                                     include_files=include_files,
                                     additional_flags=additional_flags)

        call_kwargs = dict(shell=False)

        try:
            logging.getLogger(__name__).debug(cmd)
            self.subprocess_launcher.check_output(cmd, **call_kwargs)
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


def build_robocopy_command(source, dest, exclude_files, include_files,
                           additional_flags):
    '''builds the robocopy call command.

    '''
    # Robocopy syntax:
    # robocopy <Source> <Destination> [<File>[ ...]] [<Options>]
    # - /XF: exclude files
    # - /e:  copy subdirectories
    #
    # https://docs.microsoft.com/en-us/windows-server/administration/windows-commands/robocopy
    cmd = ['robocopy', source, dest, "/e", "/COPY:DT"]

    def _is_empty(args):
        if args is None:
            return True
        if not args:
            return True
        if args == '':
            return True
        if all(val == '' for val in args):
            return True
        return False

    if not _is_empty(exclude_files):
        cmd.extend([
            '/XF',
        ] + exclude_files)

    if not _is_empty(include_files):
        cmd.extend([
            '/IF',
        ] + include_files)

    # previously known as "secure mode"
    cmd.extend(["/r:1", "/w:30", "/dcopy:T"])

    # additional flags.
    if not _is_empty(additional_flags):
        cmd.extend(additional_flags)

    return cmd


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
