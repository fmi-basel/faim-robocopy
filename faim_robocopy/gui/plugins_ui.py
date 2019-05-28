from tkinter import LabelFrame
from tkinter import Checkbutton
from tkinter import Button
from tkinter import RAISED
from tkinter import TOP
from tkinter import BOTH
from tkinter import W as TK_W_ANCHOR

from .defaults import PAD
from ..plugin_loader import is_activated_plugin
from .tooltip import ToolTip


class PluginsUi(LabelFrame):
    '''GUI section to enable/disable plugins.

    '''

    def __init__(self, parent, plugins, wrap_length=300, **kwargs):
        '''builds the folder selection frame.

        '''
        super().__init__(parent,
                         width=380,
                         height=230,
                         text="Plugins",
                         borderwidth=2,
                         relief=RAISED,
                         **kwargs)
        self.pack(side=TOP, expand=True, fill=BOTH, padx=PAD, pady=PAD)
        self.columnconfigure(0, weight=1)
        pady = (PAD // 2, PAD // 2)

        self.plugins = plugins

        def get_callback(plugin):
            '''masks the on_activation call such that it is only called when the
            plugin is activated.

            '''

            def _callback():
                '''
                '''
                if is_activated_plugin(plugin):
                    plugin.on_activation()

            return _callback

        for count, plugin in enumerate(self.plugins.values()):

            button = Checkbutton(self,
                                 text=plugin.description,
                                 wraplength=wrap_length,
                                 variable=plugin._is_active_var,
                                 command=get_callback(plugin),
                                 anchor=TK_W_ANCHOR)

            # add tooltip if information is available.
            if hasattr(plugin, 'tooltip'):
                ToolTip(button, plugin.tooltip, wraplength=500)

            # extra space for last entry.
            if count == len(self.plugins) - 1:
                pady = (PAD // 2, PAD)

            button.grid(row=count, column=0, sticky='eswn', pady=pady)

            # add button for the plugin.on_call method if available.
            if hasattr(plugin, 'on_call'):
                button = Button(self,
                                text='Run',
                                overrelief='sunken',
                                command=plugin.on_call,
                                width=4,
                                anchor='center')
                button.grid(row=count,
                            column=1,
                            sticky='we',
                            pady=pady,
                            padx=(0, PAD))
