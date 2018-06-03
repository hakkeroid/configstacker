# -*- coding: utf-8 -*-

__all__ = ['make_subdicts']


def make_subdicts(base, keychain):
    """Generate sub-dictionaries based on a keychain.

    Starting from the base dictionary for each key in the keychain
    another sub-dictionary will be added and then used as the new base
    dictionary. The result will be a chain of child dictionaries.
    At the end the innermost sub-dictionary will be returned for
    convenience.

    Args:
        base (dict): The root dictionary which will contain all
            sub-directories after this function is done.

        keychain (list): Each key of the list results in an additional
            sub-dictionary in `base`.
    Returns:
        The innermost dictionary that was created.

    Examples:
        >>> from configstacker import utils
        >>> base_dict = {}
        >>> inner_dict = utils.make_subdicts(base_dict, ['a', 'b', 'c'])
        >>> inner_dict
        {}
        >>> base_dict
        {'a': {'b': {'c': {}}}}

        >>> base_dict = {'a': {}}  # some preexisting dictionary
        >>> inner_dict = utils.make_subdicts(base_dict, ['m', 'n'])
        >>> inner_dict['x'] = 1    # some changes in the innermost dictionary
        >>> base_dict
        {'a': {}, 'm': {'n': {'x': 1}}}
    """
    for key in keychain:
        base = base.setdefault(key, {})
    return base
