'''Console frame for logging in tkinter gui.

This code is based on https://github.com/beenje/tkinter-logging-text-widget

Original licence:

Copyright (c) 2017, Benjamin Bertrand
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

'''

from tkinter.scrolledtext import ScrolledText
import tkinter as tk

import logging
import queue


class QueueHandler(logging.Handler):
    '''Class to send logging records to a queue.

    It can be used from different threads The ConsoleUi class polls
    this queue to display records in a ScrolledText widget

    '''

    def __init__(self, log_queue):
        '''
        '''
        super(QueueHandler, self).__init__()
        self.log_queue = log_queue

    def emit(self, record):
        '''
        '''
        self.log_queue.put(record)


class ConsoleUi(tk.LabelFrame):
    '''Poll messages from a logging queue and display them
    in a scrolled text widget

    '''

    def __init__(self, parent, title):
        '''
        '''
        super().__init__(parent, text=title)

        # Create a ScrolledText wdiget
        self.scrolled_text = ScrolledText(self, state='disabled')
        self.scrolled_text.pack(expand=True, fill=tk.BOTH)

        self.scrolled_text.configure(font='TkFixedFont')
        self.scrolled_text.tag_config('INFO', foreground='black')
        self.scrolled_text.tag_config('DEBUG', foreground='gray')
        self.scrolled_text.tag_config('WARNING', foreground='orange')
        self.scrolled_text.tag_config('ERROR', foreground='red')
        self.scrolled_text.tag_config(
            'CRITICAL', foreground='red', underline=1)

        # Create a logging handler using a queue and add it to the
        # _root_ logger
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter(
            '%(asctime)s: %(message)s', datefmt='%d.%m.%Y %I:%M:%S')
        self.queue_handler.setFormatter(formatter)
        logging.getLogger().addHandler(self.queue_handler)

        # Start polling messages from the queue
        self.after(100, self.poll_log_queue)

    def display(self, record):
        '''
        '''
        msg = self.queue_handler.format(record)
        self.scrolled_text.configure(state='normal')
        self.scrolled_text.insert(tk.END, msg + '\n', record.levelname)
        self.scrolled_text.configure(state='disabled')
        # Autoscroll to the bottom
        self.scrolled_text.yview(tk.END)

    def poll_log_queue(self):
        '''
        '''
        # Check every 100ms if there is a new message in the queue to display
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.after(100, self.poll_log_queue)
