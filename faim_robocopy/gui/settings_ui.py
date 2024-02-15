from collections import namedtuple

from tkinter import Toplevel
from tkinter import Frame
from tkinter import Entry
from tkinter import Label
from tkinter import Button
from tkinter import Checkbutton
from tkinter import StringVar
from tkinter import BooleanVar
from tkinter import DoubleVar
from tkinter import messagebox
from tkinter import TclError
from tkinter.ttk import Notebook

from .defaults import PAD
from .defaults import BORDERWIDTH
from .about import AboutFrame
from .tooltip import ToolTip
from .wrapping_label import WrappingLabel

from ..settings import read_custom_settings
from ..settings import write_custom_settings
from ..robocopy import build_robocopy_command

SettingsItem = namedtuple('SettingsItem',
                          ['label_text', 'variable_type', 'tooltip'])

SECTION_NAMES = {
    'email': 'E-Mail',
    'updates': 'Auto-updates',
    'default_params': 'Robocopy',
    'logging': 'Logging'
}

SETTING_NAMES = {
    'email': {
        'smtphost':
        SettingsItem('SMTP server adress', 'str',
                     'Adress of SMTP server for sending e-mail notifications'),
        'sender_address':
        SettingsItem('Sender address used for notifications', 'str', None)
    },
    'updates': {
        'check_for_update_at_startup':
        SettingsItem('Check for updates at each start', 'bool', None),
        'show_window':
        SettingsItem(
            'Show updater window', 'bool',
            'If False, the update will be run silently in the background'),
    },
    'default_params': {
        'multithreaded':
        SettingsItem('Run copy to multiple destinations in parallel', 'bool',
                     None),
        'delete_src':
        SettingsItem('Delete copied files from source', 'bool', None),
        'omit_patters':
        SettingsItem('Default file patterns to be ignored', 'str', None),
        'time_interval_in_s':
        SettingsItem('Time interval to launch robocopies in seconds', 'float',
                     None),
        'time_to_exit_in_s':
        SettingsItem('Time in seconds to wait while no change in folders',
                     'float', None),
        'custom_flags':
        SettingsItem(
            'Additional flags (e.g. for logging to a file, add: /LOG+:debug.log)', 'str',
            'Additional flags to be passed to robocopy. '
            'See the official robocopy doc for more information. '
            'Flags are passed "as-is". Use carefully.')
    },
    'logging': {
        'clean_older_than_ndays':
        SettingsItem('Remove log files that are older than n days', 'float',
                     None)
    }
}


class SettingsUi(Toplevel):
    '''
    '''

    pack_params = dict(padx=PAD, anchor='w')

    def __init__(self, parent, **kwargs):
        '''
        '''
        kwargs.update({'width': 400, 'height': 500})
        super().__init__(parent, borderwidth=BORDERWIDTH, **kwargs)
        self.title('Settings')

        self.settings = read_custom_settings()
        self.variables = {}

        # add options.
        self.add_settings_frame()

        # exit buttons.
        Button(self, text='Apply',
               command=self.apply_settings).pack(side='right',
                                                 fill='both',
                                                 anchor='e',
                                                 pady=PAD,
                                                 padx=PAD)
        Button(self, text='Cancel', command=self.cancel).pack(side='right',
                                                              fill='both',
                                                              anchor='e',
                                                              pady=PAD,
                                                              padx=PAD)

        self.minsize(kwargs['width'], kwargs['height'])

    def add_settings_frame(self):
        '''builds entry and checkbox fields for all settings.

        '''
        # Prepare tabs
        self.tabcontrol = Notebook(self)

        for section_key in (key for key in self.settings.keys()
                            if key != 'DEFAULT'):

            # create new tabs for each setting.
            section_key_name = SECTION_NAMES.get(section_key, None)
            if section_key_name is None:
                continue

            label_frame = Frame(self.tabcontrol)
            self.tabcontrol.add(label_frame, text=section_key_name)

            for key, val in self.settings[section_key].items():

                setting = SETTING_NAMES.get(section_key, {}).get(key, None)

                if setting is None:
                    continue

                if setting.variable_type == 'str':
                    variable = self._add_str_setting(label_frame, setting, val)
                elif setting.variable_type == 'bool':
                    variable = self._add_bool_setting(label_frame, setting,
                                                      val)
                elif setting.variable_type == 'float':
                    variable = self._add_numeric_setting(
                        label_frame, setting, val)

                self.variables[(section_key, key)] = variable

            if section_key == 'default_params':
                self._add_current_command(label_frame)

        # Add "About" tab:
        self.tabcontrol.add(AboutFrame(self.tabcontrol), text='About')

        # Place tabs into main window.
        self.tabcontrol.pack(fill='both', expand=True, **self.pack_params)

    def _add_current_command(self, parent):
        '''
        '''
        self._command = StringVar()
        self._update_command()
        self.variables[('default_params',
                        'custom_flags')].trace('w', self._update_command)
        Label(parent, text='Complete robocopy command:',
              anchor='w').pack(side='top', fill='x', padx=PAD)
        WrappingLabel(
            parent,
            textvariable=self._command,
            anchor='w',
            justify='left',
            wraplength=370,  # initial size
        ).pack(side='top', fill='x', padx=2 * PAD)

    def _update_command(self, *args, **kwargs):
        '''
        '''
        flags = self.variables[('default_params',
                                'custom_flags')].get().split(' ')
        flags = [x for x in flags if x != '']
        self._command.set(
            build_robocopy_command('SOURCE', 'DEST', exclude_files=['EXCL'],
                                   include_files=['INCL'],
                                   additional_flags=flags))

    def _add_str_setting(self, parent, setting_item, value):
        '''
        '''
        var = StringVar()
        var.set(value)

        lbl = Label(parent, text=setting_item.label_text, anchor='w')
        lbl.pack(side='top', fill='x', padx=PAD)
        Entry(parent, textvariable=var).pack(padx=PAD,
                                             pady=(0, PAD),
                                             side='top',
                                             expand=False,
                                             fill='x')
        if setting_item.tooltip is not None:
            ToolTip(lbl, text=setting_item.tooltip)

        return var

    def _add_bool_setting(self, parent, setting_item, value):
        '''
        '''
        var = BooleanVar()
        var.set(value)

        button = Checkbutton(parent,
                             text=setting_item.label_text,
                             variable=var,
                             anchor='w')
        button.pack(pady=(PAD / 2, PAD / 2), fill='x', **self.pack_params)
        if setting_item.tooltip is not None:
            ToolTip(button, text=setting_item.tooltip)

        return var

    def _add_numeric_setting(self, parent, setting_item, value):
        '''
        '''
        var = DoubleVar()
        var.set(value)

        lbl = Label(parent, text=setting_item.label_text, anchor='w')
        lbl.pack(side='top', fill='x', padx=PAD)
        Entry(
            parent,
            textvariable=var,
        ).pack(padx=PAD, pady=(0, PAD), side='top', expand=False, fill='x')

        if setting_item.tooltip is not None:
            ToolTip(lbl, text=setting_item.tooltip)

        return var

    def apply_settings(self):
        '''write settings and indicate that it needs a restart.

        '''
        for (section_key, key), var in self.variables.items():
            previous = self.settings[section_key][key]
            try:
                self.settings[section_key][key] = str(var.get())
            except TclError as err:
                self.settings[section_key][key] = str(previous)
                messagebox.showerror(
                    'Error', 'Could not save setting for {}: {}'.format(
                        SETTING_NAMES[section_key][key].label_text, str(err)))
                return

        write_custom_settings(self.settings)
        messagebox.showinfo(
            'Saving new settings',
            'New settings will be effective after restart of faim robocopy.')
        self.destroy()

    def cancel(self):
        '''discard changes and close.

        '''
        self.destroy()
