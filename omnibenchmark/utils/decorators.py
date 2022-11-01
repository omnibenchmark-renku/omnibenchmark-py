"""General decorators used in omnibenchmark"""

import functools
from typing import Mapping


def option_list(function):
    """
    Return an empty list, if no or only None type arguments are provided
    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        arg_list = list(args) + list(kwargs.values())
        if len(arg_list) > 0 and any(argv is not None for argv in arg_list):
            return function(*args, **kwargs)
        else:
            return []

    return wrapper


def option_str(function):
    """
    Return an empty string, if no or only None type arguments are provided
    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        arg_list = list(args) + list(kwargs.values())
        if len(arg_list) > 0 and any(argv is not None for argv in arg_list):
            return function(*args, **kwargs)
        else:
            return ""

    return wrapper


def option_dict_list(function):
    """
    Return an empty list, if none of the provided arguments is a dictionary
    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        arg_list = list(args) + list(kwargs.values())
        if len(arg_list) > 0 and all(isinstance(argv, Mapping) for argv in arg_list):
            return function(*args, **kwargs)
        else:
            return []

    return wrapper


def option_dict_none(function):
    """
    Return None, if none of the provided arguments is a dictionary
    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        arg_list = list(args) + list(kwargs.values())
        if len(arg_list) > 0 and all(isinstance(argv, Mapping) for argv in arg_list):
            return function(*args, **kwargs)
        else:
            return None

    return wrapper
