""" All kind of check or test functions to ensure correct variable inputs beyont type hinting"""

from typing import List, Iterable, Mapping, Union, Optional, overload
from omnibenchmark.utils.exceptions import InputError


def flatten(nested_list: List[Iterable]) -> List:
    """Flatten a nested list into a single list

    Args:
        nested_list (List[List]): A nested list

    Returns:
        List: A flat list
    """
    return [item for sublist in nested_list for item in sublist]


def mixed_flatten(mixed_list: List[Iterable]) -> List:
    """Flatten a list of list elements and none list elements

    Args:
        mixed_list (List[Iterable]): A list with mixed and none mixed elements

    Returns:
        List: A flat list
    """
    nested = [
        item for sublist in mixed_list if type(sublist) is list for item in sublist
    ]
    unnested = [item for item in mixed_list if type(item) is not list]
    return nested + unnested


def check_name_matching(entry1: Iterable[str], entry2: Iterable[str]):
    """Check if all entries of a list (entry2) are part of a second list (entry1) of entries

    Args:
        entry1 (List[str]): List to with variables to check
        entry2 (List[str]): List containing the variables that are allowed

    """
    if any(val not in entry1 for val in entry2):
        uniq_entry2 = list(set(entry2))
        raise InputError(f"Expected inputs from ${entry1}, but found ${uniq_entry2}")
    else:
        pass


@overload
def empty_object_to_none(obj: List) -> Optional[List]:
    ...


@overload
def empty_object_to_none(obj: Mapping) -> Optional[Mapping]:
    ...


def empty_object_to_none(obj: Union[List, Mapping]) -> Optional[Union[List, Mapping]]:
    if len(obj) == 0:
        return None
    else:
        return obj


def parse_explicit_inputs(obj: Optional[Mapping]) -> List:
    if obj is None:
        return []
    else:
        return list(obj.values())


def check_default_parameter(
    default_params: Optional[Mapping], param_combinations: Optional[List[Mapping]]
) -> Optional[Mapping]:
    """Check if the specified default parameter are part of the available parameter combinations

    Args:
        default_params (Optional[Mapping]): Default parameter mapping
        param_combinations (Optional[List[Mapping]]): List of all available parameter combinations

    Raises:
        InputError: If parameter defaults are specified, but no parameter dataset is detected.

    Returns:
        Optional[Mapping]: Default parameter mapping
    """
    if default_params is not None and (
        param_combinations is None or len(param_combinations) < 1
    ):
        raise InputError(
            "No parameter input detected, but default specified.\n"
            "Did you intend to run different parameter? If yes please check the parameter input.\n"
            "Otherwise please do not specify default parameter outside your script."
        )
    if (
        default_params is None
        or default_params in param_combinations  # type: ignore
        or len(default_params) == 0
    ):
        return default_params
    else:
        print(
            f"WARNING: The specified parameter defaults are not part of the parameter space.\n"
            f"The specified defaults will be ignored!\n"
            f"Please check your defaults:\n {default_params}\n and the parameter space:\n {param_combinations}"
        )
        return param_combinations[0]  # type: ignore


def rm_none_from_list(in_list: List) -> List:
    return [element for element in in_list if element is not None]


def elements_to_string(d: Mapping) -> Mapping:
    """Convert all non iterable elements in a dict to strings

    Args:
        d (dict): Dictionary to convert

    Returns:
        Mapping: Converted dictionary
    """
    for k, v in d.items():
        if not isinstance(v, Iterable):
            d[k] = str(v)  # type:ignore
        if type(v) is list:
            d[k] = [e if isinstance(e, Iterable) else str(e) for e in v]  # type:ignore
    return d


def elements_to_list(d: Mapping) -> Mapping:
    """Convert all non list elements in a dict to lists

    Args:
        d (dict): Dictionary to convert

    Returns:
        Mapping: Converted dictionary
    """
    for k, v in d.items():
        if not isinstance(v, list):
            d[k] = [v]  # type:ignore
    return d
