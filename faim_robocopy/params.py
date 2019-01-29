import os
import logging

PARAM_FNAME = 'param.txt'


def read_params(user_dir):
    '''read last used source and dest params.

    '''
    params = dict(source='', dest1='', dest2='')

    param_file = os.path.join(user_dir, PARAM_FNAME)
    try:
        with open(param_file, 'r') as fout:
            content = fout.read().strip('\n')
            params['source'], params['dest1'], params['dest2'] = content.split(
                ";")

    except Exception as err:
        logging.getLogger(__name__).debug(
            'Could not read parameters from %s. Error: %s', param_file,
            str(err))
    return params


def dump_params(user_dir, source, dest1, dest2):
    '''write last source and dest params

    '''
    delimiter = ';'
    param_file = os.path.join(user_dir, PARAM_FNAME)

    logging.getLogger(__name__).debug('Writing user params to %s', param_file)
    try:
        with open(param_file, 'w') as fout:
            fout.write(delimiter.join([source, dest1, dest2]))
    except Exception as err:
        logging.getLogger(__name__).error(
            'Could not write parameters to %s. Error: %s', param_file,
            str(err))
