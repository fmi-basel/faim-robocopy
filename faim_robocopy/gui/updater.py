import logging

from tkinter import Frame
from tkinter import Message
from tkinter import LabelFrame
from tkinter import Button
from tkinter import StringVar
from tkinter import Tk
from tkinter import RAISED

from faim_robocopy.utils import PROJECT_ROOT
from faim_robocopy.auto_updater import UpdateExceptions
from faim_robocopy.auto_updater import InvalidGitRepositoryError
from faim_robocopy.auto_updater import auto_update_from_git
from faim_robocopy.auto_updater import restart
from faim_robocopy.gui.defaults import PAD, BORDERWIDTH

MINWIDTH = 300
MINHEIGHT = 100

UPDATER_TITLE = 'FAIM-robocopy Updater'


class UpdaterWindow(Frame):
    '''Show a dialog while trying to fetch the latest version.

    '''

    def __init__(self, parent):
        '''
        '''
        super().__init__(
            parent, borderwidth=BORDERWIDTH, width=MINWIDTH, height=MINHEIGHT)
        self.pack(side='top', fill='both', expand=True)

        # Containing labelframe.
        label_frame = LabelFrame(
            self, text='Update status', borderwidth=2, relief=RAISED)
        label_frame.pack(fill='both', expand=True)

        #
        self.parent = parent
        self.logger = logging.getLogger(__name__)

        # Configure parent window.
        self.parent.title(UPDATER_TITLE)
        self.parent.minsize(width=MINWIDTH, height=MINHEIGHT)

        # Setup message content.
        self.content = StringVar()

        # Message view.
        self.message = Message(
            label_frame, textvariable=self.content, width=180)
        self.message.pack(
            side='left',
            padx=PAD,
            pady=PAD,
            expand=True,
            anchor='w')

        # Button.
        self.button = Button(
            label_frame, text='OK', state='disabled', command=self.close)
        self.button.pack(side='bottom', fill='both', padx=PAD, pady=PAD)

        # Register hotkey
        self.parent.bind('<Control-q>', self.quit)

        # Init done.
        self.logger.debug('Created %s', type(self).__name__)

    def request_restart(self):
        '''
        '''
        self.button.configure(command=restart, state='normal')
        self.update_idletasks()

    def set_done(self):
        '''
        '''
        self.button.configure(state='normal')
        self.parent.config(cursor='')
        self.update_idletasks()

    def set_busy(self):
        '''
        '''
        self.parent.config(cursor='watch')

    def set_status(self, message, *args):
        '''
        '''
        message = message % args
        self.logger.info(message)
        self.content.set(message)
        self.update_idletasks()

    def set_error(self, message, *args):
        '''
        '''
        message = message % args
        self.logger.error(message)
        self.content.set(message)
        self.update_idletasks()

    def close(self):
        '''
        '''
        self.logger.debug('Closing %s', type(self).__name__)
        self.parent.destroy()


def _update(interface):
    '''updates repository and communicates status through the given interface.

    '''
    interface.set_busy()
    interface.set_status('Looking for updates...')

    try:
        if auto_update_from_git(PROJECT_ROOT, remote='origin'):
            interface.set_status(
                'Fetched newest version. FAIM-Robocopy is going to restart...')
            interface.request_restart()

    except InvalidGitRepositoryError as err:
        interface.set_error('Update failed: %s is not a valid repository.',
                            str(err))
    except UpdateExceptions as err:
        interface.set_error('Update failed: %s.', str(err))
    except Exception as err:
        interface.set_error('Unexpected error during update: %s.', str(err))
    else:
        interface.set_status('Updater done.')
    finally:
        interface.set_done()


def run_updater_ui():
    '''
    '''
    root = Tk()
    window = UpdaterWindow(root)
    root.after(50, lambda: _update(window))
    root.mainloop()
