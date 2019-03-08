from tkinter import Toplevel
from tkinter import Label
from tkinter import TclError


class ToolTip:
    '''Tooltip class for tkinter.

    Implementation is inspired by cpython.idlelib's tool tip.

    '''

    x_offset = 10
    y_offset = 10

    def __init__(self, parent, text, hover_delay=1000, **label_kwargs):
        '''Creates a tooltip for the given parent.

        Parameters
        ----------
        parent : parent widget
           Parent widget onto which the tooltip is anchored.
        text : string
           Tooltip text.
        hover_delay : int
           Timedelay before the tooltip is shown.
        label_kwargs : dict
           Parameters passed on to tkinter.Label

        '''
        self.parent = parent
        self.text = text
        self.tip = None
        self._id = None
        self.hover_delay = hover_delay

        self.label_kwargs = dict(
            background='#ffffff',
            font=(None, 10),
            borderwidth=1,
            relief='solid',
            justify='left')
        self.label_kwargs.update(label_kwargs)

        self.parent.bind('<Enter>', self.schedule)
        self.parent.bind('<Leave>', self.hide)
        self.parent.bind('<ButtonPress>', self.hide)

    def schedule(self, event):
        '''schedule a show after a certain delay.

        '''
        self.unschedule()
        self._id = self.parent.after(self.hover_delay,
                                     lambda: self.show(event))

    def unschedule(self):
        '''cancel potentially scheduled `shows`.

        '''
        old_id = self._id
        self._id = None
        if old_id is not None:
            self.parent.after_cancel(old_id)

    def show(self, event):
        '''show tooltip.

        '''
        if self.tip:  # already showing.
            return

        x, y, dx, dy = self.parent.bbox('insert')
        x = x + dx + self.parent.winfo_rootx() + event.x + self.x_offset
        y = y + dy + self.parent.winfo_rooty() + event.y + self.y_offset
        self.tip = Toplevel(self.parent)
        self.tip.wm_overrideredirect(1)

        self.tip.wm_geometry("+%d+%d" % (x, y))
        label = Label(self.tip, text=self.text, **self.label_kwargs)
        label.pack(ipadx=1)

    def hide(self, event):
        '''remove tooltip.

        '''
        self.unschedule()
        tip_buffer = self.tip
        self.tip = None

        if tip_buffer is None:
            return

        try:
            tip_buffer.destroy()
        except TclError:
            pass
