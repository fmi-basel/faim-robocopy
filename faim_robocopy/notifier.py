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
        pass

    @abc.abstractmethod
    def finished(self, source, destinations):
        '''notify finish.
        '''
        pass


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
                    'Please check the logfile in {} for further information.\n'
                    'Note that further errors will not be reported by mail.'.
                    format(self.logfile), **self.smtp_kwargs)

            self.fail_count += 1

    def finished(self, source, destinations):
        '''
        '''
        # yapf: disable
        send_mail(self.user_mail, self._get_finish_headline(),
                  'The robocopy task on host {} '.format(get_hostname()) +
                  'with source:\n  {}\n'.format(source) +
                  'and destination{}:\n  '.format('s' if len(destinations) >= 2 else '') +
                  '\n  '.join(destinations) +
                  '\nfinished.\n' +
                  'Please check summary in {}'.format(self.logfile),
                  **self.smtp_kwargs)
        # yapf: enable

    def _get_finish_headline(self):
        '''construct head of finish-notification.

        '''
        base = 'Robocopy Info: RobocopyTask terminated'

        if self.fail_count == 0:
            return base + ' successfully'

        return base + ' with {} errors'.format(self.fail_count)
