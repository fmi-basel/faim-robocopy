from tkinter import LabelFrame
from tkinter import Label
from tkinter import Button
from tkinter.filedialog import askdirectory

from tkinter import W as TK_W_ANCHOR
from tkinter import RAISED
from tkinter import SUNKEN
from tkinter import BOTH
from tkinter import TOP

from .defaults import PAD


def choose_directory(initial_val):
    '''open a dialog to select a folder.

    '''
    return askdirectory(
        initialdir=initial_val, title="Please select a directory")


class FolderSelectionUi(LabelFrame):
    '''GUI section to choose source and destination folders.

    '''

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

        pack_params = dict(
            side=TOP, expand=False, anchor=TK_W_ANCHOR, padx=PAD)

        # source folder
        self.source_button = Button(
            self,
            text='Source directory',
            overrelief=SUNKEN,
            command=self._choose_source,
            width=20,
            anchor=TK_W_ANCHOR)
        self.source_button.pack(pady=(PAD, 0), **pack_params)

        self.source_txt_label = Label(
            self, textvariable=self.shared.source_var, anchor=TK_W_ANCHOR)
        self.source_txt_label.pack(**pack_params)

        # destination 1 folder
        self.dest1_button = Button(
            self,
            text='Destination 1 directory',
            overrelief=SUNKEN,
            command=self._choose_first_dest,
            anchor=TK_W_ANCHOR,
            width=20)
        self.dest1_button.pack(pady=(2 * PAD, 0), **pack_params)
        self.dest1_txt_label = Label(
            self, textvariable=self.shared.dest1_var, anchor=TK_W_ANCHOR)
        self.dest1_txt_label.pack(**pack_params)

        # Destination 2 folder selection
        self.dest2_button = Button(
            self,
            text='Destination 2 directory',
            overrelief=SUNKEN,
            command=self._choose_second_dest,
            anchor=TK_W_ANCHOR,
            width=20)
        self.dest2_button.pack(pady=(2 * PAD, 0), **pack_params)
        self.dest2_txt_label = Label(
            self, textvariable=self.shared.dest2_var, anchor=TK_W_ANCHOR)
        self.dest2_txt_label.pack(pady=(0, PAD), **pack_params)

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
