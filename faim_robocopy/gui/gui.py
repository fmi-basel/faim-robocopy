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

from faim_robocopy import __version__
from ..plugin_loader import collect_plugins
from ..plugin_loader import is_activated_plugin
from ..plugin_loader import initialize_plugin

from ..utils import get_user_info
from ..robocopy import RobocopyTask
from ..notifier import MailNotifier
from ..params import read_params, dump_params

from .defaults import PAD, BORDERWIDTH
from .callback_decorator import decorate_callback
from .shared_resources import SharedResources
from .folder_selection import FolderSelectionUi
from .options import OptionsSelectionUi
from .console import ConsoleUi
from .settings_ui import SettingsUi
from .plugins_ui import PluginsUi


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
    def __init__(self, parent, logfile, settings):
        '''initialize gui.

        '''
        super().__init__(parent)
        self.parent = parent
        self.logfile = logfile

        self.user_info = get_user_info()
        self.settings = settings
        self.shared = SharedResources(user_mail=self.user_info['user_mail'],
                                      **read_params(
                                          self.user_info['user_dir']))
        self.shared.update_from_settings(self.settings)

        # Init tasks.
        self.robocopy = RobocopyTask(None)

        # Init plugins.
        self.plugins = {
            key: initialize_plugin(plugin, self.shared)
            for key, plugin in collect_plugins().items()
        }

        # construct interface.
        self.build(parent)

        # set minimum size of window.
        self.parent.update_idletasks()
        self.parent.minsize(self.parent.winfo_width(),
                            self.parent.winfo_height())

    def build(self, parent):
        '''builds all components of the GUI.

        '''
        Frame.__init__(self,
                       parent,
                       width=780,
                       height=580,
                       borderwidth=BORDERWIDTH)
        self.pack(side=TOP, fill=BOTH, expand=True)

        self.horizontal_panes = PanedWindow(self, orient=HORIZONTAL)
        self.vertical_panes = PanedWindow(self.horizontal_panes,
                                          orient=VERTICAL)
        self.folder_frame = FolderSelectionUi(self.vertical_panes, self.shared)
        self.options_frame = OptionsSelectionUi(self.vertical_panes,
                                                self.shared)

        self.vertical_panes.add(self.folder_frame)
        self.vertical_panes.add(self.options_frame)
        if self.plugins:
            self.plugins_frame = PluginsUi(self.vertical_panes, self.plugins)
            self.vertical_panes.add(self.plugins_frame)

        self.vertical_panes.pack(side=LEFT,
                                 expand=True,
                                 fill=BOTH,
                                 padx=PAD,
                                 pady=PAD)

        self.console_frame = ConsoleUi(self.horizontal_panes, 'Summary')
        self.console_frame.pack(side=TOP,
                                expand=True,
                                fill=BOTH,
                                padx=PAD,
                                pady=PAD)

        self.horizontal_panes.add(self.vertical_panes)
        self.horizontal_panes.add(self.console_frame)
        self.horizontal_panes.pack(expand=True, fill=BOTH, padx=PAD, pady=PAD)

        # Settings window.
        self.settings_gui = None

        # add buttons
        self.add_copy_and_abort()

        # register quit's
        self.parent.protocol('WM_DELETE_WINDOW', self.quit)
        self.parent.bind('<Control-q>', self.quit)

    def add_copy_and_abort(self):
        '''adds the copy and abort buttons to the bottom of the gui.

        '''
        button_params = dict(width=8, overrelief=RIDGE, font="arial 10")
        self.copy_button = Button(self,
                                  text='Copy',
                                  command=self.do_copy,
                                  **button_params)
        self.copy_button.config(bg="yellow green",
                                fg="black",
                                disabledforeground='darkgrey')
        self.copy_button.pack(side=LEFT, padx=PAD, pady=PAD)

        self.cancel_button = Button(self,
                                    text='Abort',
                                    command=self.abort,
                                    state='disable',
                                    **button_params)
        self.cancel_button.config(background='tomato',
                                  activeforeground='black',
                                  disabledforeground='darkgrey')
        self.cancel_button.pack(side=LEFT, padx=PAD, pady=PAD)

        self.settings_button = Button(self,
                                      text='Settings',
                                      command=self.open_settings,
                                      **button_params)
        self.settings_button.pack(side='right', padx=PAD, pady=PAD)

    def do_copy(self):
        '''callback for running the copy.

        '''
        robocopy_kwargs = self.shared.get_robocopy_kwargs()

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
        dump_params(user_dir=self.user_info['user_dir'],
                    source=self.shared.source_var.get(),
                    dest1=self.shared.dest1_var.get(),
                    dest2=self.shared.dest2_var.get())

        self.robocopy = RobocopyTask(
            notifier=MailNotifier(user_mail=self.shared.mail_var.get(),
                                  logfile=self.logfile,
                                  **self.settings.get_mail_kwargs()),
            additional_flags=self.settings.get_robocopy_flags())
        self.robocopy_thread = Thread(target=decorate_callback(
            self.robocopy.run, self._enter_toggle, self._exit_toggle),
                                      kwargs=robocopy_kwargs)
        self.robocopy_thread.start()

    def open_settings(self):
        '''launches the settings gui.

        '''
        if self.settings_gui is not None and self.settings_gui.winfo_exists():
            return
        self.settings_gui = SettingsUi(self.parent)

    def abort(self):
        '''stop running robocopy processes. This is where the default parameters
        can be modified.

        '''
        logging.getLogger(__name__).info(
            'Robocopy aborted by user. Please wait ...')
        self._stop_robocopy_task()
        logging.getLogger(__name__).info('... abort done.')

    def quit(self, *args):
        '''exit gui and clean-up running robocopy processes.

        '''
        logging.getLogger(__name__).info('FAIM-robocopy terminated by user')
        self._stop_robocopy_task()
        self.parent.destroy()

    def _enter_toggle(self):
        '''toggle active/disabled state of buttons before robocopy call.

        '''
        self.copy_button.configure(state='disable')
        self.cancel_button.configure(state='normal')

    def _exit_toggle(self):
        '''toggle active/disabled state of buttons at exit of robocopy call.

        '''
        try:
            self.copy_button.configure(state='normal')
            self.cancel_button.configure(state='disable')

            try:
                for plugin_name, plugin in self.plugins.items():
                    # TODO add check for activation
                    if is_activated_plugin(plugin):
                        plugin.on_task_end()
            except Exception as err:
                logging.getLogger(__name__).error(
                    'Plugin %s failed with error: %s', plugin_name, str(err))

        # ignore errors that arise from trying to switch the state
        # when the UI is already closed.
        except RuntimeError as err:
            if 'main thread is not in main loop' in str(err):
                pass
            else:
                raise

    def _stop_robocopy_task(self):
        '''stop all worker threads.

        '''
        self.robocopy.terminate()