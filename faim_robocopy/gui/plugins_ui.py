from tkinter import LabelFrame
from tkinter import Checkbutton
from tkinter import RAISED
from tkinter import TOP
from tkinter import BOTH
from tkinter import W as TK_W_ANCHOR

from .defaults import PAD


class PluginsUi(LabelFrame):
    '''GUI section to enable/disable plugins.

    '''

    def __init__(self, parent, plugins, wrap_length=300, **kwargs):
        '''builds the folder selection frame.

        '''
        super().__init__(
            parent,
            width=380,
            height=230,
            text="Plugins",
            borderwidth=2,
            relief=RAISED,
            **kwargs)
        self.pack(side=TOP, expand=True, fill=BOTH, padx=PAD, pady=PAD)
        pack_params = dict(side=TOP, expand=False, fill='x')

        self.plugins = plugins

        for _, plugin in self.plugins.items():
            button = Checkbutton(
                self,
                text=plugin.description,
                wraplength=wrap_length,
                variable=plugin._is_active_var,
                anchor=TK_W_ANCHOR)
            button.pack(pady=(0, PAD), **pack_params)
