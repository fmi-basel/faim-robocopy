import os
import logging

from tkinter import Tk
from tkinter import Frame
from tkinter import PanedWindow
from tkinter import Button
from tkinter import LEFT
from tkinter import BOTH
from tkinter import TOP
from tkinter import RIDGE
from tkinter import HORIZONTAL, VERTICAL
from tkinter import messagebox

from threading import Thread

import psutil

from faim_robocopy.utils import get_user_info
from faim_robocopy.gui.console import ConsoleUi
from faim_robocopy.robocopy import RobocopyTask
from faim_robocopy.notifier import MailNotifier

from faim_robocopy.params import read_params, dump_params
from faim_robocopy import __version__
from faim_robocopy.gui.defaults import PAD, BORDERWIDTH
from faim_robocopy.gui.callback_decorator import decorate_callback

from .shared_resources import SharedResources
from .folder_selection import FolderSelectionUi
from .options import OptionsSelectionUi


def get_window_name():
    return 'Robocopy FAIM - v{}'.format(__version__)


def error_message(message):
    '''show an error message in a separate window.

    '''
    root = Tk()
    root.withdraw()
    messagebox.showerror(title='Problem', message=message)
    root.destroy()


class RobocopyGUI(Frame):
    '''Main GUI.

    '''

    def __init__(self, parent, logfile):
        '''initialize gui.

        '''
        super().__init__(parent)
        self.parent = parent
        self.logfile = logfile
        self.user_info = get_user_info()
        self.shared = SharedResources(
            user_mail=self.user_info['user_mail'],
            **read_params(self.user_info['user_dir']))
        self.robocopy = RobocopyTask()

        self.build(parent)

        # set minimum size of window.
        self.parent.update_idletasks()
        self.parent.minsize(self.parent.winfo_width(),
                            self.parent.winfo_height())

    def build(self, parent):
        '''builds all components of the GUI.

        '''
        Frame.__init__(
            self, parent, width=780, height=580, borderwidth=BORDERWIDTH)
        self.pack(side=TOP, fill=BOTH, expand=True)

        self.horizontal_panes = PanedWindow(self, orient=HORIZONTAL)
        self.vertical_panes = PanedWindow(
            self.horizontal_panes, orient=VERTICAL)
        self.folder_frame = FolderSelectionUi(self.vertical_panes, self.shared)
        self.options_frame = OptionsSelectionUi(self.vertical_panes,
                                                self.shared)
        self.vertical_panes.add(self.folder_frame)
        self.vertical_panes.add(self.options_frame)
        self.vertical_panes.pack(
            side=LEFT, expand=True, fill=BOTH, padx=PAD, pady=PAD)

        self.console_frame = ConsoleUi(self.horizontal_panes, 'Summary')
        self.console_frame.pack(
            side=TOP, expand=True, fill=BOTH, padx=PAD, pady=PAD)

        self.horizontal_panes.add(self.vertical_panes)
        self.horizontal_panes.add(self.console_frame)
        self.horizontal_panes.pack(expand=True, fill=BOTH, padx=PAD, pady=PAD)

        # add buttons
        self.add_copy_and_abort()

        # register quit's
        self.parent.protocol('WM_DELETE_WINDOW', self.quit)
        self.parent.bind('<Control-q>', self.quit)

    def add_copy_and_abort(self):
        '''adds the copy and abort buttons to the bottom of the gui.

        '''
        self.copy_button = Button(
            self,
            text='Copy',
            width=8,
            overrelief=RIDGE,
            font="arial 10",
            command=self.do_copy)
        self.copy_button.config(
            bg="yellow green", fg="black", disabledforeground='darkgrey')
        self.copy_button.pack(side=LEFT, padx=PAD, pady=PAD)
        self.cancel_button = Button(
            self,
            text='Abort',
            width=8,
            overrelief=RIDGE,
            font="arial 10",
            command=self.abort,
            state='disable')
        self.cancel_button.config(
            background='tomato',
            activeforeground='black',
            disabledforeground='darkgrey')
        self.cancel_button.pack(side=LEFT, padx=PAD, pady=PAD)

    def do_copy(self):
        '''callback for running the copy.

        '''
        robocopy_kwargs = dict(
            source=self.shared.source_var.get(),
            destinations=[
                self.shared.dest1_var.get(),
                self.shared.dest2_var.get()
            ],
            multithread=self.shared.multithreaded_var.get(),
            time_interval=self.shared.time_interval_var.get(),
            wait_exit=self.shared.time_exit_var.get(),
            delete_source=self.shared.delete_src_var.get(),
            notifier=MailNotifier(
                user_mail=self.shared.mail_var.get(), logfile=self.logfile),
            exclude_files=self.shared.omit_files_var.get(),
            silent=self.shared.silent_var.get(),
            secure_mode=self.shared.secure_mode_var.get())

        if robocopy_kwargs['source'] == '' or not os.path.exists(
                robocopy_kwargs['source']):
            error_message('You must select a source folder')
            return

        if all((dest == '' or not os.path.exists(dest))
               for dest in robocopy_kwargs['destinations']):
            error_message('You must specify at least one destination folder')
            return

        if self.robocopy.is_running():
            logging.getLogger(__name__).info(
                'Robocopy is already running. Consider aborting and restarting'
                ' to update its parameters.')
            return

        # save parameters for future use.
        # TODO Shouldnt we save all settings?
        dump_params(
            user_dir=self.user_info['user_dir'],
            source=self.shared.source_var.get(),
            dest1=self.shared.dest1_var.get(),
            dest2=self.shared.dest2_var.get())

        self.robocopy = RobocopyTask()
        self.robocopy_thread = Thread(
            target=decorate_callback(self.robocopy.run,
                                     self._enter_toggle_buttons,
                                     self._exit_toggle_buttons),
            kwargs=robocopy_kwargs)
        self.robocopy_thread.start()

    def abort(self):
        '''stop running robocopy processes.

        '''
        logging.getLogger(__name__).info(
            'Robocopy aborted by user. Please wait ...')
        self._stop_running_threads()
        self._stop_robocopy_processes()
        logging.getLogger(__name__).info('... done')

    def quit(self, *args):
        '''exit gui and clean-up running robocopy processes.

        '''
        logging.getLogger(__name__).info('FAIM-robocopy terminated by user')
        self._stop_running_threads()
        self._stop_robocopy_processes()
        self.parent.destroy()

    def _enter_toggle_buttons(self):
        '''toggle active/disabled state of buttons before robocopy call.

        '''
        self.copy_button.configure(state='disable')
        self.cancel_button.configure(state='normal')

    def _exit_toggle_buttons(self):
        '''toggle active/disabled state of buttons at exit of robocopy call.

        '''
        try:
            self.copy_button.configure(state='normal')
            self.cancel_button.configure(state='disable')

        # ignore errors that arise from trying to switch the state
        # when the UI is already closed.
        except RuntimeError as err:
            if 'main thread is not in main loop' in str(err):
                pass
            else:
                raise

    def _stop_running_threads(self):
        '''stop all worker threads.

        '''
        self.robocopy.terminate()
        # if self.robocopy_thread.is_alive():
        #     self.robocopy_thread.join()

    @staticmethod
    def _stop_robocopy_processes():
        '''terminate all running robocopy processes and windows consoles.

        '''
        # Legacy code
        # TODO Check if this works / is needed.
        # TODO Doesnt this cause issues with other instances of robocopy?
        for proc in psutil.process_iter():
            try:
                if proc.name() == 'Robocopy.exe':
                    psutil.Process(proc.pid).terminate()
                #elif proc.name() == 'conhost.exe':
                #    psutil.Process(proc.pid).terminate()
            except psutil.Error as err:
                logging.getLogger(__name__).error(
                    'Could not terminate process %s. Error message: %s',
                    proc.name(), str(err))
