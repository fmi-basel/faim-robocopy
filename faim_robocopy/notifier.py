import abc
from threading import Lock

from .mail import send_mail
from .utils import get_hostname


class BaseNotifier(metaclass=abc.ABCMeta):
    '''Abstract notifier class.

    '''
    @abc.abstractmethod
    def failed(self):
        '''notify failure.
        '''

    @abc.abstractmethod
    def finished(self, source, destinations):
        '''notify finish.
        '''


class MailNotifier(BaseNotifier):
    '''informs user per mail about progress and failures.

    In case of an error, the user is informed exactly once.

    '''
    def __init__(self, user_mail, logfile, smtphost, sender_address):
        '''
        '''
        self.user_mail = user_mail
        self._lock = Lock()
        self.fail_count = 0
        self.logfile = logfile
        self.smtp_kwargs = dict(smtphost=smtphost,
                                sender_address=sender_address)

    def failed(self, error):
        '''
        '''
        with self._lock:
            if self.fail_count <= 0:
                send_mail(
                    self.user_mail, 'Robocopy Info: ERROR',
                    str(error) + '\n\n'
                    f'Please check the logfile in {self.logfile} for further information.\n'
                    'Note that further errors will not be reported by mail.', **self.smtp_kwargs)

            self.fail_count += 1

    def finished(self, source, destinations):
        '''
        '''
        # yapf: disable
        send_mail(self.user_mail, self._get_finish_headline(),
                  f'The robocopy task on host {get_hostname()} ' +
                  f'with source:\n  {source}\n' +
                  'and destination{}:\n  '.format('s' if len(destinations) >= 2 else '') +
                  '\n  '.join(destinations) +
                  '\nfinished.\n' +
                  f'Please check summary in {self.logfile}',
                  **self.smtp_kwargs)
        # yapf: enable

    def _get_finish_headline(self):
        '''construct head of finish-notification.

        '''
        base = 'Robocopy Info: RobocopyTask terminated'

        if self.fail_count == 0:
            return base + ' successfully'

        return base + f' with {self.fail_count} errors'
