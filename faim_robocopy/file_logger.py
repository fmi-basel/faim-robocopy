import logging


def add_logging_to_file(filename):
    '''adds a FileHandler to the root logger.
 
    '''
    handler = logging.FileHandler(filename)
    formatter = logging.Formatter('<p>%(asctime)s: %(message)s</p>')
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
