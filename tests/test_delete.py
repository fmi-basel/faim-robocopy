import os

import pytest

from faim_robocopy.utils import delete_existing
from faim_robocopy.utils import delete_files_older_than


def test_delete_duplicates(tmpdir):
    '''test deleting of copied files.

    '''
    # setup
    source = tmpdir.mkdir('source_dir')
    dest1 = tmpdir.mkdir('dest_dir_1')
    dest2 = tmpdir.mkdir('some_other_dir').mkdir('dest_dir_2')

    # Add some empty folders
    empties = [source.mkdir('non').mkdir('sense'), source.mkdir('is_empty')]
    empties_not_for_deletion = [
        dest1.mkdir('nonsense'),
    ]

    files_in = {
        source: ['a.txt', 'b.ini', 'some.txt', 'thing.txt'],
        dest1: ['a.txt', 'b.ini', 'some.txt', 'another.txt'],
        dest2: ['b.ini', 'thing.txt']
    }

    for folder in files_in.keys():
        for filename in files_in[folder]:
            filehandle = folder.join(filename)
            filehandle.write(filename)

    delete_existing(source, [dest1, dest2])

    # check that all files exists.
    for folder in [dest1, dest2]:
        for filename in files_in[folder]:
            assert os.path.exists(os.path.join(folder, filename))

    for filename in files_in[source]:
        if filename == 'b.ini':  # this should have been deleted!
            continue
        assert os.path.exists(os.path.join(source, filename))

    # check that copied file is removed from source.
    assert not os.path.exists(os.path.join(source, 'b.ini'))

    # check if empty folders are treated correctly.
    for empty_dir in empties:
        assert os.path.exists(empty_dir)

    for empty_dir in empties_not_for_deletion:
        assert os.path.exists(empty_dir)


def test_delete_duplicates_diff(tmpdir):
    '''test deleting of copied files with unidentical contents.

    '''
    # setup.
    source = tmpdir.mkdir('source_dir')
    dest1 = tmpdir.mkdir('dest_dir_1')
    dest2 = tmpdir.mkdir('some_other_dir').mkdir('dest_dir_2')

    files_in = {
        source: [
            'a.txt',
        ],
        dest1: [
            'a.txt',
        ],
        dest2: [
            'a.txt',
        ]
    }

    # create files.
    for (folder, filename) in ((folder, filename)
                               for folder, files_in_folder in files_in.items()
                               for filename in files_in_folder):
        filehandle = folder.join(filename)
        filehandle.write(filename)

        # create different content for each file.
        # NOTE this is going to lead to differently sized files due to
        # the different lengths of the content string
        filehandle.write_text(str(folder), encoding='utf-8')

    # do the work.
    delete_existing(source, [dest1, dest2])

    # check that all files exists.
    for folder in [dest1, dest2]:
        for filename in files_in[folder]:
            assert os.path.exists(os.path.join(folder, filename))

    for filename in files_in[source]:
        assert os.path.exists(os.path.join(source, filename))


def test_delete_older_than(tmpdir):
    '''test deleting of old files.

    '''
    # setup
    folder = tmpdir.mkdir('some_dir')

    path = folder.join('old_file.txt')
    path.write('stuff')

    delete_files_older_than(folder, '*txt', -0.001)
    assert not os.path.exists(path)


def test_not_delete_older_than(tmpdir):
    '''test deleting of old files.

    '''
    # setup
    folder = tmpdir.mkdir('some_dir')

    path = folder.join('fresh_file.txt')
    path.write('stuff')

    delete_files_older_than(folder, '*txt', 1)
    assert os.path.exists(path)


def test_delete_older_than_n_with_pattern(tmpdir):
    '''test deleting of old files.

    '''
    # setup
    folder = tmpdir.mkdir('some_dir')

    excluded_paths = [
        folder.join(fname)
        for fname in ['mismatch.txt', 'another.png', 'something']
    ]

    included_paths = [
        folder.join(fname)
        for fname in ['some_match.txt', 'another_match.png']
    ]

    for path in excluded_paths + included_paths:
        path.write('stuff')

    delete_files_older_than(folder, '*_match.*', -0.001)
    for path in excluded_paths:
        assert os.path.exists(path)

    for path in included_paths:
        assert not os.path.exists(path)
