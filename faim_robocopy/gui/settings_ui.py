from collections import namedtuple

from tkinter import Toplevel
from tkinter import LabelFrame
from tkinter import Entry
from tkinter import Label
from tkinter import Button
from tkinter import Checkbutton
from tkinter import RAISED
from tkinter import StringVar
from tkinter import BooleanVar
from tkinter import DoubleVar
from tkinter import messagebox
from tkinter import TclError

from .defaults import PAD
from .defaults import BORDERWIDTH

from ..settings import read_custom_settings
from ..settings import write_custom_settings

SettingsItem = namedtuple('SettingsItem',
                          ['label_text', 'variable_type', 'tooltip'])

SECTION_NAMES = {
    'email': 'E-Mail',
    'updates': 'Auto-updates',
    'default_params': 'Default parameters'
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
        'secure_mode':
        SettingsItem('Use secure mode by default', 'bool', None),
        'multithreaded':
        SettingsItem('Run copy to multiple destinations in parallel', 'bool',
                     None),
        'delete_src':
        SettingsItem('Delete copied files from source', 'bool', None),
        'omit_patters':
        SettingsItem('Default file patterns to be ignored', 'str', None),
        'time_interval_in_s':
        SettingsItem('Time interval to launch robocopies in s', 'float', None),
        'time_to_exit_in_s':
        SettingsItem('Time in s to wait while no chang ein folders', 'float',
                     None)
    }
}


def _check_numeric(parent, val):
    '''check if entered value is numeric.

    '''
    try:
        float(val)
        return True
    except ValueError:
        return False


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
        Button(
            self, text='Apply', command=self.apply_settings).pack(
                side='right', fill='both', anchor='e', pady=PAD, padx=PAD)
        Button(
            self, text='Cancel', command=self.cancel).pack(
                side='right', fill='both', anchor='e', pady=PAD, padx=PAD)

        self.minsize(kwargs['width'], kwargs['height'])

    def add_settings_frame(self):
        '''builds entry and checkbox fields for all settings.

        '''
        for section_key in (key for key in self.settings.keys()
                            if key is not 'DEFAULT'):

            label_frame = LabelFrame(
                self,
                text=SECTION_NAMES[section_key],
                borderwidth=2,
                relief=RAISED)
            label_frame.pack(fill='both', expand=True, **self.pack_params)

            for key, val in self.settings[section_key].items():

                setting = SETTING_NAMES.get(section_key, None).get(key, None)

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

    def _add_str_setting(self, parent, setting_item, value):
        '''
        '''
        var = StringVar()
        var.set(value)

        Label(
            parent, text=setting_item.label_text, anchor='w').pack(
                side='top', fill='x', padx=PAD)
        Entry(
            parent, textvariable=var).pack(
                padx=PAD, pady=(0, PAD), side='top', expand=False, fill='x')

        return var

    def _add_bool_setting(self, parent, setting_item, value):
        '''
        '''
        var = BooleanVar()
        var.set(value)

        Checkbutton(
            parent, text=setting_item.label_text, variable=var,
            anchor='w').pack(
                pady=(PAD / 2, PAD / 2), fill='x', **self.pack_params)
        return var

    def _add_numeric_setting(self, parent, setting_item, value):
        '''
        '''
        var = DoubleVar()
        var.set(value)

        Label(
            parent, text=setting_item.label_text, anchor='w').pack(
                side='top', fill='x', padx=PAD)
        Entry(
            parent,
            textvariable=var,
            # validate='focusout',
            # validatecommand=_check_numeric
        ).pack(
            padx=PAD, pady=(0, PAD), side='top', expand=False, fill='x')

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

    def cancel(self):
        '''discard changes and close.

        '''
        self.destroy()
