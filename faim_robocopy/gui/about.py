from tkinter import Frame
from tkinter import Label

from .defaults import PAD
from faim_robocopy import __version__

TITLE = 'FAIM-Robocopy'
ABOUT_TEXT = [
    "FAIM-Robocopy is developped at the Facility for Advanced Imaging and Microscopy (FAIM) of the Friedrich Miescher Institute for Biomedical Research by:",
    "Laurent Gelman, Jan Eglinger and Markus Rempfler"
]


class AboutFrame(Frame):
    def __init__(self, master=None, **kwargs):
        '''
        '''
        super().__init__(master=master, **kwargs)

        width = kwargs.get('width', 350)

        Label(
            self,
            text=TITLE,
            font=('Arial', 18),
        ).pack(pady=(3 * PAD, PAD))
        Label(
            self,
            text='Version: ' + __version__,
        ).pack(pady=(PAD // 2, PAD // 2))

        pady = (PAD, 0)
        for text in ABOUT_TEXT:
            Label(self, text=text, justify='left',
                  wraplength=width).pack(pady=pady)
            pady = (1, PAD)
