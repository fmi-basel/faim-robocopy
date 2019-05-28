from tkinter import Label


class WrappingLabel(Label):
    '''Label with automatic adaptation of wraplength with resizing container.


    Based on discussion in:
    https://www.reddit.com/r/learnpython/comments/6dndqz/how_would_you_make_text_that_automatically_wraps/
    '''

    def __init__(self, parent, **kwargs):
        '''
        '''
        super().__init__(parent, **kwargs)
        self.bind('<Configure>', lambda e: self.config(wraplength=self.
                                                       winfo_width()))
