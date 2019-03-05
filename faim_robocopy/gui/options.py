from tkinter import LabelFrame
from tkinter import Label
from tkinter import Checkbutton
from tkinter import Entry

from tkinter import W as TK_W_ANCHOR
from tkinter import X as TK_X
from tkinter import RAISED
from tkinter import LEFT
from tkinter import BOTH
from tkinter import TOP

from .defaults import PAD


class OptionsSelectionUi(LabelFrame):
    '''
    '''

    def __init__(self, parent, shared, wrap_length=300, **kwargs):
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

        # Options checkboxes
        self.secure_mode_button = Checkbutton(
            self,
            text="Secure Mode (slower)",
            wraplength=wrap_length,
            variable=self.shared.secure_mode_var,
            anchor=TK_W_ANCHOR)
        self.secure_mode_button.pack(pady=(0, PAD), **pack_params)

        self.multithreaded_button = Checkbutton(
            self,
            text="Copy both destinations in parallel",
            wraplength=wrap_length,
            variable=self.shared.multithreaded_var,
            anchor=TK_W_ANCHOR)
        self.multithreaded_button.pack(pady=(0, PAD), **pack_params)

        self.silent_button = Checkbutton(
            self,
            text="Show Robocopy console",
            wraplength=wrap_length,
            variable=self.shared.silent_var,
            anchor=TK_W_ANCHOR)
        self.silent_button.pack(pady=(0, PAD), **pack_params)

        self.delete_src_button = Checkbutton(
            self,
            text="Delete files in source folder after copy",
            wraplength=wrap_length,
            variable=self.shared.delete_src_var,
            anchor=TK_W_ANCHOR)
        self.delete_src_button.pack(pady=(0, PAD), **pack_params)

        self.omit_files_label = Label(
            self, text="Omit files with extension:", anchor=TK_W_ANCHOR)
        self.omit_files_label.pack(**pack_params)
        self.omit_files_box = Entry(
            self, width=3, textvariable=self.shared.omit_files_var)
        self.omit_files_box.pack(pady=(0, PAD), **pack_params)

        # Time-lapse information
        self.time_interval_label = Label(
            self,
            text="Time interval between Robocopy processes (min):",
            anchor=TK_W_ANCHOR)
        self.time_interval_label.pack(**pack_params)
        self.time_interval_box = Entry(
            self, width=6, textvariable=self.shared.time_interval_var)
        self.time_interval_box.pack(pady=(0, PAD), **pack_params)

        # Time-Exit information
        self.time_exit_label = Label(
            self,
            text="Time for exiting if no change in folders (min):",
            anchor=TK_W_ANCHOR)
        self.time_exit_label.pack(**pack_params)
        self.time_exit_box = Entry(
            self, width=6, textvariable=self.shared.time_exit_var)
        self.time_exit_box.pack(pady=(0, PAD), **pack_params)

        # E-mail information
        self.mail_label = Label(
            self, text="Send Summary to:", anchor=TK_W_ANCHOR)
        self.mail_label.pack(**pack_params)
        self.mail_box = Entry(
            self, justify=LEFT, width=25, textvariable=self.shared.mail_var)
        self.mail_box.pack(**pack_params)
