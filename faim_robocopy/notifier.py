import abc

from faim_robocopy.mail import send_mail


class BaseNotifier(metaclass=abc.ABCMeta):
    '''Abstract notifier class.

    '''

    @abc.abstractmethod
    def failed(self):
        '''notify failure.
        '''
        pass

    @abc.abstractmethod
    def finished(self):
        '''notify finish.
        '''
        pass


class MailNotifier(BaseNotifier):
    '''informs user per mail about progress.

    In case of an error, the user is informed exactly once.

    '''

    def __init__(self, user_mail, logfile):
        '''
        '''
        self.user_mail = user_mail
        self.fail_count = 0
        self.logfile = logfile

    def failed(self, error):
        '''
        '''
        if self.fail_count <= 0:
            send_mail(
                self.user_mail, 'Robocopy Info: ERROR',
                'Please check summary in {}.\n'
                'Note that further errors will not be reported by mail.'.
                format(self.logfile))

        self.fail_count += 1

    def finished(self):
        '''
        '''
        send_mail(self.user_mail, self._get_finish_headline(),
                  'Please check summary in {}'.format(self.logfile))

    def _get_finish_headline(self):
        '''construct head of finish-notification.

        '''
        base = 'Robocopy Info: RobocopyTask terminated'

        if self.fail_count == 0:
            return base + ' successfully'

        return base + ' with {} errors'.format(self.fail_count)
