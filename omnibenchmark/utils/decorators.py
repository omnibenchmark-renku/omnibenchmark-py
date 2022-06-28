"""General decorators used in omnibenchmark"""

import functools
from typing import Mapping


def option_list(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        arg_list = list(args) + list(kwargs.values())
        if len(arg_list) > 0 and any(argv is not None for argv in arg_list):
            return function(*args, **kwargs)
        else:
            return []

    return wrapper


def option_str(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        arg_list = list(args) + list(kwargs.values())
        if len(arg_list) > 0 and any(argv is not None for argv in arg_list):
            return function(*args, **kwargs)
        else:
            return ""

    return wrapper


def option_dict_list(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        arg_list = list(args) + list(kwargs.values())
        if len(arg_list) > 0 and all(isinstance(argv, Mapping) for argv in arg_list):
            return function(*args, **kwargs)
        else:
            return []

    return wrapper


def option_dict_none(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        arg_list = list(args) + list(kwargs.values())
        if len(arg_list) > 0 and all(isinstance(argv, Mapping) for argv in arg_list):
            return function(*args, **kwargs)
        else:
            return None

    return wrapper
