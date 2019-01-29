import datetime
import os
import sys
import logging
import signal
import psutil

from tkinter import Tk
from tkinter import Frame
from tkinter import LabelFrame
from tkinter import PanedWindow
from tkinter import Label
from tkinter import Button
from tkinter import Checkbutton
from tkinter import Entry
from tkinter import StringVar
from tkinter import DoubleVar
from tkinter import IntVar
from tkinter import RAISED
from tkinter import SUNKEN
from tkinter import LEFT
from tkinter import BOTH
from tkinter import TOP
from tkinter import RIDGE
from tkinter import HORIZONTAL, VERTICAL
from tkinter import W as TK_W_ANCHOR
from tkinter import X as TK_X
from tkinter import messagebox
from tkinter.filedialog import askdirectory

from threading import Thread

from faim_robocopy.utils import get_user_info
from faim_robocopy.utils import count_files_in_subtree
from faim_robocopy.console import ConsoleUi
from faim_robocopy.robocopy import RobocopyTask
from faim_robocopy.file_logger import add_logging_to_file


def choose_directory(initial_val):
    '''open a dialog to select a folder.

    '''
    return askdirectory(
        initialdir=initial_val, title="Please select a directory")


PARAM_FNAME = 'param.txt'


def _read_params(user_dir):
    '''read last used source and dest params.

    '''
    params = dict(source='', dest1='', dest2='')

    # TODO make this more robust.
    paramFile = os.path.join(user_dir, PARAM_FNAME)
    if os.path.isfile(paramFile):
        with open(paramFile, 'r') as target:
            content = target.read().strip('\n')
            params['source'], params['dest1'], params['dest2'] = content.split(
                ";")
    return params


def _dump_params(user_dir, source, dest1, dest2):
    '''write last source and dest params

    '''
    delimiter = ';'
    param_file = os.path.join(user_dir, PARAM_FNAME)

    logging.getLogger(__name__).debug('Writing user params to %s', param_file)

    with open(param_file, 'w') as fout:
        fout.write(delimiter.join([source, dest1, dest2]))


def _get_logpath(user_info):
    '''constructs the logfile path.

    '''
    # Locations to check. high-priority first.
    potential_logdirs = [user_info.get('homeshare'), user_info.get('user_dir')]
    _subdir = 'Desktop'

    logfilename = 'Robocopy_Logfile_{}.html'.format(
        datetime.datetime.now().strftime("%H-%M-%S"))

    # check locations to log to:
    for logdir in (os.path.join(basedir, _subdir)
                   for basedir in potential_logdirs if basedir is not None):
        if os.path.exists(logdir):
            return os.path.join(logdir, logfilename)

    raise IOError('Could not determine logfile path.')


BORDERWIDTH = 5
PAD = 10


class SharedResources(object):
    '''manages shared variables.

    '''

    def __init__(self, source, dest1, dest2, user_mail):
        '''
        '''
        self.source_var = StringVar()
        self.source_var.set(source)

        self.dest1_var = StringVar()
        self.dest1_var.set(dest1)

        self.dest2_var = StringVar()
        self.dest2_var.set(dest2)

        self.secure_mode_var = IntVar()
        self.secure_mode_var.set(1)

        self.multithreaded_var = IntVar()
        self.multithreaded_var.set(0)

        self.silent_var = IntVar()
        self.silent_var.set(0)

        self.delete_src_var = IntVar()
        self.delete_src_var.set(0)

        self.omit_files_var = StringVar()
        self.omit_files_var.set('')

        self.time_interval_var = DoubleVar()
        self.time_interval_var.set(0.5)

        self.time_exit_var = DoubleVar()
        self.time_exit_var.set(5)

        self.mail_var = StringVar()
        self.mail_var.set(user_mail)


class FolderSelectionUi(LabelFrame):
    def __init__(self, parent, shared, **kwargs):
        '''builds the folder selection frame.

        '''
        self.shared = shared

        super().__init__(
            parent,
            width=380,
            height=230,
            text="Folder Selection",
            borderwidth=2,
            relief=RAISED,
            **kwargs)
        self.pack(side=TOP, expand=True, fill=BOTH, padx=PAD, pady=PAD)

        # source folder
        self.source_button = Button(
            self,
            text='Source directory',
            overrelief=SUNKEN,
            command=self._choose_source,
            width=20,
            anchor=TK_W_ANCHOR)
        self.source_button.pack()
        self.source_button.place(x=5, y=5)

        self.source_txt_label = Label(
            self,
            textvariable=self.shared.source_var,
            width=50,
            anchor=TK_W_ANCHOR)
        self.source_txt_label.pack()
        self.source_txt_label.place(x=5, y=35)

        # destination 1 folder
        self.dest1_button = Button(
            self,
            text='Destination 1 directory',
            overrelief=SUNKEN,
            command=self._choose_first_dest,
            width=20)
        self.dest1_button.pack()
        self.dest1_button.place(x=5, y=70)
        self.dest1_txt_label = Label(
            self,
            textvariable=self.shared.dest1_var,
            width=50,
            anchor=TK_W_ANCHOR)
        self.dest1_txt_label.pack()
        self.dest1_txt_label.place(x=5, y=100)

        # Destination 2 folder selection
        self.dest2_button = Button(
            self,
            text='Destination 2 directory',
            overrelief=SUNKEN,
            command=self._choose_second_dest,
            width=20)
        self.dest2_button.pack()
        self.dest2_button.place(x=5, y=135)
        self.dest2_txt_label = Label(
            self,
            textvariable=self.shared.dest2_var,
            width=50,
            anchor=TK_W_ANCHOR)
        self.dest2_txt_label.pack()
        self.dest2_txt_label.place(x=5, y=165)

    def _choose_source(self):
        '''callback to set source.

        '''
        val = choose_directory(self.shared.source_var.get())
        self.shared.source_var.set(val)

    def _choose_first_dest(self):
        '''callback to set dest1.

        '''
        val = choose_directory(self.shared.dest1_var.get())
        self.shared.dest1_var.set(val)

    def _choose_second_dest(self):
        '''callback to set dest2.

        '''
        val = choose_directory(self.shared.dest2_var.get())
        self.shared.dest2_var.set(val)


class OptionsSelectionUi(LabelFrame):
    '''
    '''

    # TODO Fix positioning.

    def __init__(self, parent, shared, **kwargs):
        '''
        '''
        self.shared = shared
        super().__init__(
            parent,
            width=380,
            height=235,
            text="Option Selection",
            borderwidth=2,
            relief=RAISED,
            **kwargs)
        self.pack(side=TOP, expand=True, fill=BOTH, padx=PAD, pady=PAD)

        pack_params = dict(side=TOP, expand=False, fill=TK_X)
        WRAPLENGTH = 300

        # Options checkboxes
        self.secure_mode_button = Checkbutton(
            self,
            text="Secure Mode (slower)",
            wraplength=WRAPLENGTH,
            variable=self.shared.secure_mode_var,
            anchor=TK_W_ANCHOR)
        self.secure_mode_button.pack(pady=(0, PAD), **pack_params)
        #self.secure_mode_button.place(x=5, y=5)

        self.multithreaded_button = Checkbutton(
            self,
            text="Copy both destinations in parallel",
            wraplength=WRAPLENGTH,
            variable=self.shared.multithreaded_var,
            anchor=TK_W_ANCHOR)
        self.multithreaded_button.pack(pady=(0, PAD), **pack_params)
        #self.multithreaded_button.place(x=5, y=30)

        self.silent_button = Checkbutton(
            self,
            text="Show Robocopy console",
            wraplength=WRAPLENGTH,
            variable=self.shared.silent_var,
            anchor=TK_W_ANCHOR)
        self.silent_button.pack(pady=(0, PAD), **pack_params)
        #self.silent_button.place(x=5, y=55)

        self.delete_src_button = Checkbutton(
            self,
            text="Delete files in source folder after copy",
            wraplength=WRAPLENGTH,
            variable=self.shared.delete_src_var,
            anchor=TK_W_ANCHOR)
        self.delete_src_button.pack(pady=(0, PAD), **pack_params)
        #self.delete_src_button.place(x=5, y=80)

        self.omit_files_label = Label(
            self, text="Omit files with extension:", anchor=TK_W_ANCHOR)
        self.omit_files_label.pack(**pack_params)
        #self.omit_files_label.place(x=5, y=105)
        self.omit_files_box = Entry(
            self, width=3, textvariable=self.shared.omit_files_var)
        self.omit_files_box.pack(pady=(0, PAD), **pack_params)
        #self.omit_files_box.place(x=280, y=105)

        # Time-lapse information
        self.time_interval_label = Label(
            self,
            text="Time interval between Robocopy processes (min):",
            anchor=TK_W_ANCHOR)
        self.time_interval_label.pack(**pack_params)
        #self.time_interval_label.place(x=5, y=130)
        self.time_interval_box = Entry(
            self, width=6, textvariable=self.shared.time_interval_var)
        self.time_interval_box.pack(pady=(0, PAD), **pack_params)
        #self.time_interval_box.place(x=280, y=132)

        # Time-Exit information
        self.time_exit_label = Label(
            self,
            text="Time for exiting if no change in folders (min):",
            anchor=TK_W_ANCHOR)
        self.time_exit_label.pack(**pack_params)
        #self.time_exit_label.place(x=5, y=155)
        self.time_exit_box = Entry(
            self, width=6, textvariable=self.shared.time_exit_var)
        self.time_exit_box.pack(pady=(0, PAD), **pack_params)
        #self.time_exit_box.place(x=280, y=157)

        # E-mail information
        self.mail_label = Label(
            self, text="Send Summary to:", anchor=TK_W_ANCHOR)
        self.mail_label.pack(**pack_params)
        #self.mail_label.place(x=5, y=180)
        self.mail_box = Entry(
            self, justify=LEFT, width=25, textvariable=self.shared.mail_var)
        self.mail_box.pack(**pack_params)
        #self.mail_box.place(x=115, y=182)


class RobocopyGUI(Frame):
    '''
    '''

    def __init__(self, parent):
        '''
        '''
        self.parent = parent
        self.user_info = get_user_info()
        self.shared = SharedResources(
            user_mail=self.user_info['user_mail'],
            **_read_params(self.user_info['user_dir']))
        self.robocopy = RobocopyTask()

        add_logging_to_file(_get_logpath(self.user_info))

        self.build(parent)

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

        self.add_copy_and_abort()

        self.parent.protocol('WM_DELETE_WINDOW', self.quit)
        self.parent.bind('<Control-q>', self.quit)

    def add_copy_and_abort(self):
        '''adds the copy and abort buttons to the bottom of the gui.

        '''
        self.copy_button = Button(
            self,
            text='Do Copy !',
            width=8,
            overrelief=RIDGE,
            font="arial 10",
            command=self.do_copy)
        self.copy_button.config(bg="yellow green", fg="black")
        self.copy_button.pack(side=LEFT, padx=PAD, pady=PAD)
        self.cancel_button = Button(
            self,
            text='Abort',
            width=8,
            overrelief=RIDGE,
            font="arial 10",
            command=self.abort)
        self.cancel_button.config(bg="tomato", fg="black")
        self.cancel_button.pack(side=LEFT, padx=PAD, pady=PAD)

    def error_message(self, message):
        '''show an error message in a separate window.

        '''
        root = Tk()
        root.withdraw()
        messagebox.showerror(title='Problem', message=message)
        root.destroy()

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
            user_mail=self.shared.mail_var.get(),
            skip_files=self.shared.omit_files_var.get(),
            silent=self.shared.silent_var.get(),
            secure_mode=self.shared.secure_mode_var.get())

        if robocopy_kwargs['source'] == '' or not os.path.exists(
                robocopy_kwargs['source']):
            return self.error_message('You must select a source folder')

        if all((dest == '' or not os.path.exists(dest))
               for dest in robocopy_kwargs['destinations']):
            return self.error_message(
                'You must specify at least one destination folder')

        if self.robocopy.is_running():
            logging.getLogger(__name__).info(
                'Robocopy is already running. Consider "Abort" to update its parameters'
            )
            return

        # save parameters for future use.
        # TODO Shouldnt we save all settings?
        _dump_params(
            user_dir=self.user_info['user_dir'],
            source=self.shared.source_var.get(),
            dest1=self.shared.dest1_var.get(),
            dest2=self.shared.dest2_var.get())

        self.robocopy = RobocopyTask()
        self.robocopy_thread = Thread(
            target=self.robocopy.run, kwargs=robocopy_kwargs)
        self.robocopy_thread.start()

        # TODO Terminate GUI?

    def abort(self):
        '''
        '''
        logging.getLogger(__name__).info('Robocopy aborted by user')
        # TODO send_mail() to user
        self._stop_running_threads()
        self._stop_robocopy_processes()

    def quit(self, *args):
        '''
        '''
        logging.getLogger(__name__).info('FAIM-robocopy terminated by user')
        self._stop_running_threads()
        self.parent.destroy()

    def _stop_running_threads(self):
        '''stop all worker threads.

        '''
        try:
            self.robocopy.terminate()
            # if self.robocopy_thread.is_alive():
            #     self.robocopy_thread.join()
        except Exception:
            pass

    def _stop_robocopy_processes(self):
        '''terminate all running robocopy processes and windows consoles.

        '''
        # Legacy code
        # TODO Check if this works
        for proc in psutil.process_iter():
            try:
                if proc.name() == 'Robocopy.exe':
                    psutil.Process(proc.pid).terminate()
                elif proc.name() == 'conhost.exe':
                    psutil.Process(proc.pid).terminate()
            except psutil.Error as err:
                logging.getLogger(__name__).error(
                    'Could not terminate process %s. Error message: %s',
                    proc.name(), str(err))


def run_robocopy_gui():
    '''
    '''
    # Legacy code: redirect standard output streams
    # TODO Is this really needed?
    if sys.executable.endswith("pythonw.exe"):
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(
            os.path.join(
                os.getenv("TEMP"), "stderr-" + os.path.basename(sys.argv[0])),
            "w")

    # Start root
    root = Tk()
    root.title("Robocopy FAIM")
    RobocopyGUI(root)
    root.mainloop()
