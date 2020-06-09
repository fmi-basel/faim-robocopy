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
from .tooltip import ToolTip


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
        self.multithreaded_button = Checkbutton(
            self,
            text="Copy both destinations in parallel",
            wraplength=wrap_length,
            variable=self.shared.multithreaded_var,
            anchor=TK_W_ANCHOR)
        self.multithreaded_button.pack(pady=(PAD // 2, PAD), **pack_params)

        self.delete_src_button = Checkbutton(
            self,
            text="Delete files in source folder after copy",
            wraplength=wrap_length,
            variable=self.shared.delete_src_var,
            anchor=TK_W_ANCHOR)
        self.delete_src_button.pack(pady=(0, PAD), **pack_params)

        # Exclude patterns
        self.omit_files_label = Label(
            self,
            text="Omit files matching the following patterns:",
            anchor=TK_W_ANCHOR)
        ToolTip(
            self.omit_files_label,
            'Separate multiple patterns with semicolons and use wildcards '
            'like * to match several files. '
            'Example: *.tif; some*.hdf5; test.csv',
            wraplength=500)
        self.omit_files_label.pack(**pack_params)
        self.omit_files_box = Entry(
            self, width=3, textvariable=self.shared.omit_files_var)
        self.omit_files_box.pack(pady=(0, PAD), **pack_params)

        # Include patterns
        self.include_files_label = Label(
            self,
            text="Include *only* files matching the following patterns:",
            anchor=TK_W_ANCHOR)
        ToolTip(
            self.include_files_label,
            'Separate multiple patterns with semicolons and use wildcards '
            'like * to match several files. \n'
            'Example: *s10_*; *s11_*; *s37_* \n'
            'Leave this field empty if you want to copy all files in the '
            'source folder.', wraplength=500)
        self.include_files_label.pack(**pack_params)
        self.include_files_box = Entry(
            self, width=3, textvariable=self.shared.include_only_files_var)
        self.include_files_box.pack(pady=(0, PAD), **pack_params)

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
