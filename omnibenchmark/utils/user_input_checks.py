""" All kind of check or test functions to ensure correct variable inputs beyont type hinting"""

from typing import List, Iterable, Mapping, Union, Optional, overload, Any
from omnibenchmark.utils.exceptions import InputError


def flatten(nested_list: List[Iterable]) -> List:
    """Flatten a nested list into a single list

    Args:
        nested_list (List[List]): A nested list

    Returns:
        List: A flat list
    """
    return [item for sublist in nested_list for item in sublist]


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

def check_default_parameter(default_params: Optional[Mapping], param_combinations: Optional[List[Mapping]]) -> Optional[Mapping]:
    if default_params is not None and (param_combinations is None or len(param_combinations) < 1):
        raise InputError(
            f'No parameter input detected, but default specified.\n'
            f'Did you intend to run different parameter? If yes please check the parameter input.\n'
            f'Otherwise please do not specify default parameter outside your script.'
        )
    if default_params is None or default_params in param_combinations or len(default_params) == 0:          #type: ignore
        return default_params
    else:
        print(
            f'WARNING: The specified parameter defaults are not part of the parameter space.\n'
            f'The specified defaults will be ignored!\n'
            f'Please check your defaults:\n {default_params}\n and the parameter space:\n {param_combinations}'
        )
        return param_combinations[0]                                            #type: ignore

