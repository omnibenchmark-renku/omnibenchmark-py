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
