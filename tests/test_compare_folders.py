import pytest

from faim_robocopy.utils import is_filetree_a_subset_of
from faim_robocopy.utils import count_identical_files
from faim_robocopy.file_filter import create_file_filter, NoFilter


def test_no_filter():
    '''
    '''
    files = ['a.txt', 'some/thing/b.csv', 'win\\dows\\file']
    assert files == create_file_filter(None)(files)
    assert files == create_file_filter('')(files)
    assert files == create_file_filter([])(files)

    assert files == create_file_filter('txt')(files)
    assert files == create_file_filter('?')(files)
    assert files == create_file_filter('.csv')(files)
    assert files == NoFilter(files)


def test_ignore_patterns():
    '''
    '''
    files = ['a.txt', 'some/thing/b.csv', 'win\\dows\\file', 'some/txt/file']

    assert files[1:] == create_file_filter('*.txt')(files)
    assert files[1:] == create_file_filter(['spam', '*.txt'])(files)
    assert [
        files[0],
    ] + files[2:] == create_file_filter('*.csv')(files)
    assert files[-2:] == create_file_filter(['*.txt', '*thing*'])(files)


def test_include_patterns():
    '''
    '''
    files = ['a.txt', 'some/thing/b.csv', 'win\\dows\\file', 'some/txt/file']

    assert files[:1] == create_file_filter(include_patterns='*.txt')(files)
    assert files[:1] == create_file_filter(include_patterns=['*.txt'])(files)
    assert files[:2] == create_file_filter(
        include_patterns=['*.txt', '*.csv'])(files)
    assert files[-2:] == create_file_filter(include_patterns=['*file'])(files)
    assert files[1:2] == create_file_filter(include_patterns=['*b.*'])(files)


def test_both_patterns():
    '''test file filter with both ignore and involve patterns.
    '''
    files = ['a.txt', 'some/thing/b.csv', 'win\\dows\\file', 'some/txt/file']

    assert [files[0],
            files[-1]] == create_file_filter(
                ignore_patterns=['win*'],
                include_patterns=['*file', 'a.*'])(files)


def test_compare(tmpdir):
    '''test comparison of subtrees.

    '''
    # setup
    source = tmpdir.mkdir('source_dir')
    dest1 = tmpdir.mkdir('some_other_dir').mkdir('dest_dir')

    file_filter = create_file_filter('*.tif')

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

    assert is_filetree_a_subset_of(source, dest1, file_filter)

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

    assert is_filetree_a_subset_of(source, dest1, file_filter)

    new_subdir = source.mkdir('new')
    assert not is_filetree_a_subset_of(source, dest1, file_filter)

    dest1.mkdir('new')
    assert is_filetree_a_subset_of(source, dest1, file_filter)

    # add a file that should be ignored
    filename = 'something.tif'
    filehandle = new_subdir.join(filename)
    filehandle.write(filename)

    assert is_filetree_a_subset_of(source, dest1, file_filter)

    filename = 'something_more.csv'
    filehandle = new_subdir.join(filename)
    filehandle.write(filename)

    assert not is_filetree_a_subset_of(source, dest1, file_filter)


def test_count_identical(tmpdir):
    '''test counting of identical files.

    '''
    # setup
    source = tmpdir.mkdir('source_dir')
    dest1 = tmpdir.mkdir('some_other_dir').mkdir('dest_dir')

    file_filter = create_file_filter('*.tif')

    files_in = {
        source: ['a.txt', 'b.ini', 'some.txt', 'image.tif'],
        dest1: ['a.txt', 'b.ini', 'some.txt', 'image.tif'],
    }

    # create stuff
    for folder in files_in.keys():
        for filename in files_in[folder]:
            filehandle = folder.join(filename)
            filehandle.write(filename)

    # do some testing
    assert count_identical_files(source, dest1, file_filter) == 3
    assert count_identical_files(source, dest1) == 4
