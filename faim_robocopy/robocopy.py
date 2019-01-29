import logging
import subprocess
import os
import datetime
import time

from concurrent.futures import ThreadPoolExecutor

from faim_robocopy.utils import compsubfolders
from faim_robocopy.utils import delete_existing
from faim_robocopy.utils import count_files_in_subtree
from faim_robocopy.mail import send_mail


class RobocopyTask(object):
    '''
    '''

    def __init__(self):
        '''
        '''
        self._running = False
        self._update_rate_in_s = 5.

    def terminate(self):
        '''requests the task to terminate.

        '''
        if self.is_running():
            logging.getLogger(__name__).warning('Stopping robocopy task')
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

    def __exit__(self, type, value, traceback):
        '''
        '''
        self._running = False

    def run(self, *args, **kwargs):
        '''
        '''
        with self:
            return self._run(*args, **kwargs)

    def _run(self, source, destinations, multithread, time_interval, wait_exit,
             delete_source, user_mail, skip_files, **robocopy_kwargs):
        '''
        '''
        # check number of dest
        if not isinstance(destinations, (tuple, list)):
            destinations = [destinations]
        destinations = [
            dest for dest in destinations
            if dest != '' and os.path.exists(dest)
        ]

        if len(destinations) == 0:
            raise RuntimeError('Need at least one destination to copy to.')

        logging.getLogger(__name__).info('Source folder: %s', source)
        for ii, dest in enumerate(destinations):
            logging.getLogger(__name__).info('Destination folder %d: %s',
                                             ii + 1, dest)

        # Define the number of threads for copying
        if multithread and len(dest) >= 2:
            max_workers = 2
        else:
            max_workers = 1

        # Log start
        logger = logging.getLogger(__name__)

        with ThreadPoolExecutor(max_workers=max_workers) as thread_pool:

            self._update_changed()

            futures = {
                dest: thread_pool.submit(
                    robocopy_call,
                    source=source,
                    dest=dest,
                    skip_files=skip_files,
                    **robocopy_kwargs)
                for dest in destinations
                #if not compsubfolders(source, dest, skip_files)
            }

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
                        # the failing job had.
                        logger.error('Robocopy failed with error %s',
                                     str(error))
                        # TODO discuss if we want to send a mail here already.
                    else:
                        logger.debug('Robocopy job terminated successfully')

            # Monitor source and dest folders and start robocopy jobs
            # whenever a source and destination have different content.
            while self.is_running():

                # Terminate if wait_exit is expired without any new
                # file to copy.
                if self._wait_has_expired(wait_exit * 60.):
                    logger.info('Stopping robocopy after %1.1f min of waiting',
                                wait_exit)
                    break

                # For all those futures that are finished, we check if
                # there are new files.
                for dest in destinations:

                    if not compsubfolders(source, dest, skip_files):
                        self._update_changed()

                        if futures[dest].done():
                            futures[dest] = thread_pool.submit(
                                robocopy_call,
                                source=source,
                                dest=dest,
                                skip_files=skip_files,
                                **robocopy_kwargs)
                            futures[dest].add_done_callback(_robocopy_callback)

                # delete files that are copied to all destinations.
                if delete_source:
                    delete_existing(source, destinations)

                # wait
                logger.info(
                    'Waiting for %1.1f min before checking for next Robocopy',
                    float(time_interval))

                # Sleep with polling for a potential terminate() signal
                for _ in range(
                        int(time_interval * 60. / self._update_rate_in_s)):
                    time.sleep(self._update_rate_in_s)
                    if not self.is_running():
                        break

        # Report files in both folders.
        logger.info('Robocopy summary:')
        for folder in [
                source,
        ] + destinations:

            if folder == '':
                continue

            try:
                filecount = count_files_in_subtree(folder)
                logging.getLogger(__name__).info('Number of files in %s = %d',
                                                 folder, filecount)
            except Exception:
                logging.getLogger(__name__).error(
                    'Could not count files in %s', folder)

        # TODO Send summary to user?


def robocopy_call(source, dest, silent, secure_mode, skip_files, dry=False):
    '''run an individual robocopy call.

    '''
    exclude_files = "*." + skip_files  # TODO Refactor

    # Robocopy syntax:
    # robocopy <Source> <Destination> [<File>[ ...]] [<Options>]
    # - /XF: exclude files
    # - /e:  copy subdirectories
    #
    # https://docs.microsoft.com/en-us/windows-server/administration/windows-commands/robocopy
    cmd = ["robocopy", source, dest, "/XF", exclude_files, "/e", "/COPY:DT"]

    if secure_mode == 1:
        cmd.append("/r:0")
        cmd.append("/w:30")
        cmd.append("/dcopy:T")
        cmd.append("/Z")

    if dry:
        logging.getLogger(__name__).info(cmd)
        return
    if silent == 0:
        FNULL = open(os.devnull, 'w')
        subprocess.check_call(cmd, stdout=FNULL, stderr=subprocess.STDOUT)
    else:
        subprocess.check_call(cmd)
