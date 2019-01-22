import logging
import subprocess
import os
import datetime
import time

from concurrent.futures import ThreadPoolExecutor

from faim_robocopy.utils import compsubfolders
from faim_robocopy.utils import delete_existing
from faim_robocopy.mail import send_mail


def robocopy(source, destinations, multithread, time_interval, wait_exit,
             delete_source, user_mail, skip_files, **robocopy_kwargs):
    '''
    '''
    # check number of dest
    if not isinstance(destinations, (tuple, list)):
        destinations = [destinations]
    destinations = [
        dest for dest in destinations if dest != '' and os.path.exists(dest)
    ]

    if len(destinations) == 0:
        raise RuntimeError('Need at least one destination to copy to.')

    logging.getLogger(__name__).info('Robocopy source folders:  source = %s',
                                     source)
    for ii, dest in enumerate(destinations):
        logging.getLogger(__name__).info('Robocopy dest %d folder: %s', ii + 1,
                                         dest)

    # Define the number of threads for copying
    if multithread and len(dest) >= 2:
        max_workers = 2
    else:
        max_workers = 1

    # Log start
    logger = logging.getLogger(__name__)
    logger.info('Copy process started')

    with ThreadPoolExecutor(max_workers=max_workers) as thread_pool:

        time_at_last_change = datetime.datetime.now()
        time_to_exit = wait_exit * 60.  # in seconds

        futures = {
            dest: thread_pool.submit(
                robocopy_call, source=source, dest=dest, **robocopy_kwargs)
            for dest in destinations
            if not compsubfolders(source, dest, skip_files)
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
                    # NOTE unfortunately, we dont know which destination the
                    # failing job had
                    logger.error('Robocopy failed with error %s', str(error))
                    # TODO discuss if we want to send a mail here already.
                else:
                    logger.info('Robocopy job terminated successfully')

        # Monitor source and dest folders and start robocopy jobs
        # whenever a source and destination have different content.
        while (datetime.datetime.now() -
               time_at_last_change).total_seconds() < time_to_exit:

            for dest in destinations:

                # For all those futures that are finished, we check if
                # there are new files.
                if not compsubfolders(source, dest, skip_files):
                    time_at_last_change = datetime.datetime.now()

                    if futures[dest].done():
                        futures[dest] = thread_pool.submit(
                            robocopy_call,
                            source=source,
                            dest=dest,
                            **robocopy_kwargs)

            # wait
            logging.getLogger(__name__).info(
                'Waiting for %1.1f min before next Robocopy', float(time_interval))
            time.sleep(time_interval * 60)

            # TODO delete files that are copied to all destinations.
            if delete_source:
                delete_existing(source, destinations)


def robocopy_call(source, dest, silent, secure_mode, skip_files, dry=True):
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
        subprocess.call(cmd, stdout=FNULL, stderr=subprocess.STDOUT)
    else:
        subprocess.call(cmd)
