import os

import pytest

from faim_robocopy.utils import delete_existing


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

    delete_existing(str(source), [str(dest1), str(dest2)])

    # check that all files exists.
    for folder in [dest1, dest2]:
        for filename in files_in[folder]:
            assert os.path.exists(os.path.join(str(folder), filename))

    for filename in files_in[source]:
        if filename == 'b.ini':  # this should have been deleted!
            continue
        assert os.path.exists(os.path.join(str(source), filename))

    # check that copied file is removed from source.
    assert not os.path.exists(os.path.join(str(source), 'b.ini'))

    # check if empty folders are treated correctly.
    for empty_dir in empties:
        assert os.path.exists(str(empty_dir))

    for empty_dir in empties_not_for_deletion:
        assert os.path.exists(str(empty_dir))


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
    for counter, (folder, filename) in enumerate(
        (folder, filename) for folder, files_in_folder in files_in.items()
            for filename in files_in_folder):
        # for filename in files_in[folder]:
        filehandle = folder.join(filename)
        filehandle.write(filename)

        # create different content for each file.
        # NOTE this is going to lead to differently sized files due to
        # the different lengths of the content string
        filehandle.write_text(str(folder), encoding='utf-8')

    # do the work.
    delete_existing(str(source), [str(dest1), str(dest2)])

    # check that all files exists.
    for folder in [dest1, dest2]:
        for filename in files_in[folder]:
            assert os.path.exists(os.path.join(str(folder), filename))

    for filename in files_in[source]:
        assert os.path.exists(os.path.join(str(source), filename))
