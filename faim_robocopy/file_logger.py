import logging

def add_logging_to_file(filename):
    '''
    '''
    handler = logging.FileHandler(filename)
    # formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    # handler.setFormatter(handler)
    logging.getLogger().addHandler(handler)
    
