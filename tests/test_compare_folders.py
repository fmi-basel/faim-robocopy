import pytest

from faim_robocopy.utils import compsubfolders


def test_compare(tmpdir):
    '''test comparison of subtrees.

    '''
    # setup
    source = tmpdir.mkdir('source_dir')
    dest1 = tmpdir.mkdir('some_other_dir').mkdir('/dest_dir')

    omit_file = 'tif'

    files_in = {
        source: [
            'a.txt',
            'b.ini',
            'some.txt',
        ],
        dest1: [
            'a.txt',
            'b.ini',
            'some.txt',
        ],
    }

    for folder in files_in.keys():
        for filename in files_in[folder]:
            filehandle = folder.join(filename)
            filehandle.write(filename)

    assert compsubfolders(str(source), str(dest1), omit_file)

    subfolder_files = {
        'some_subdir': ['b.txt', 'c.txt'],
        'some_other_subdir': ['d.txt', 'e.tiff']
    }

    for folder in files_in.keys():
        for subfolder in subfolder_files.keys():
            subfolder_h = folder.mkdir(subfolder)
            for filename in subfolder_files[subfolder]:
                filehandle = subfolder_h.join(filename)
                filehandle.write(filename)

    assert compsubfolders(str(source), str(dest1), omit_file)

    new_subdir = source.mkdir('new')
    assert not compsubfolders(str(source), str(dest1), omit_file)

    dest1.mkdir('new')
    assert compsubfolders(str(source), str(dest1), omit_file)

    # add a file that should be ignored
    filename = 'something.tif'
    filehandle = new_subdir.join(filename)
    filehandle.write(filename)

    assert compsubfolders(str(source), str(dest1), omit_file)

    filename = 'something_more.csv'
    filehandle = new_subdir.join(filename)
    filehandle.write(filename)

    assert not compsubfolders(str(source), str(dest1), omit_file)
