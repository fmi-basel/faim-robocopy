from fnmatch import fnmatch


def _is_empty(patterns):
    '''returns True if patterns is considered an empty pattern list.
    '''
    if patterns == '':
        return True
    if patterns is None:
        return True
    if all(pat == '' for pat in patterns):
        return True
    if not patterns:
        return True
    return False


def create_file_filter(ignore_patterns=None, include_patterns=None):
    '''creates a file filter that removes files that match any
    of the given patterns.

    '''
    if isinstance(ignore_patterns, str):
        ignore_patterns = [ignore_patterns,]
    if isinstance(include_patterns, str):
        include_patterns = [include_patterns,]
    if _is_empty(ignore_patterns) and _is_empty(include_patterns):
        return NoFilter

    return FileFilter(ignore_patterns=ignore_patterns,
                      include_patterns=include_patterns)


class FileFilter:
    def __init__(self, ignore_patterns=None, include_patterns=None):
        '''filters a list of filenames such that only those files remain that:

        match any of of the include_patterns
        match none of the ignore_patterns

        '''
        self.ignore_patterns = ignore_patterns if not _is_empty(
            ignore_patterns) else None
        self.include_patterns = include_patterns if not _is_empty(
            include_patterns) else None

    def _include(self, item):
        '''returns True if the item matches any include_pattern.
        '''
        if self.include_patterns is None:
            return True
        return any(fnmatch(item, pat) for pat in self.include_patterns)

    def _exclude(self, item):
        '''returns True if the item matches any ignore_pattern.
        '''
        if self.ignore_patterns is None:
            return False
        return any(fnmatch(item, pat) for pat in self.ignore_patterns)

    def __call__(self, file_list):
        '''run the filter on the given list.

        Parameters
        ----------
        file_list : list of paths
            list of paths to be filtered.

        Returns
        -------
        filtered_files : list of paths
            filtered file list.

        '''
        return [
            item for item in file_list
            if self._include(item) and not self._exclude(item)
        ]


def NoFilter(file_list):
    '''Doesnt filter anything.
    '''
    return file_list
