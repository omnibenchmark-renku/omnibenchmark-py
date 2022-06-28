"""Everything related to parameter filtering and handling"""

from typing import Any, Mapping, List, Optional, Dict
from omnibenchmark.utils.exceptions import ParameterError
import itertools
import json


def apply_filter(value_list: List, filter_vals) -> List:
    if isinstance(filter_vals, Dict):
        if any(key not in ["upper", "lower", "exclude"] for key in filter_vals.keys()):
            print(
                f"WARNING: Invalid filter keys.\n"
                f"Please use 'upper', 'lower', 'exclude' only: {filter_vals.keys()}"
            )
        if "upper" in filter_vals.keys():
            try:
                value_list = [
                    int(x) for x in value_list if int(x) <= int(filter_vals["upper"])
                ]
            except:
                raise ParameterError(
                    f'Could not apply filtering of {filter_vals["upper"]}.\n'
                    f"Please check if all values can be converted into a numeric: {value_list}.\n"
                    f'Use the "except" filer key otherwise.'
                )

        if "lower" in filter_vals.keys():
            try:
                value_list = [
                    int(x) for x in value_list if int(x) >= int(filter_vals["lower"])
                ]
            except:
                raise ParameterError(
                    f'Could not apply filtering of {filter_vals["lower"]}.\n'
                    f"Please check if all values can be converted into a numeric: {value_list}.\n"
                    f'Use the "except" filer key otherwise.'
                )
        if "exclude" in filter_vals.keys():
            if isinstance(filter_vals["exclude"], List):
                filter_ex_string = [str(x) for x in filter_vals["exclude"]]
            else:
                filter_ex_string = str(filter_vals["exclude"])  # type: ignore
            value_list = [x for x in value_list if str(x) not in filter_ex_string]
    else:
        if isinstance(filter_vals, List):
            filter_list = [str(x) for x in filter_vals]
        else:
            filter_list = str(filter_vals)  # type: ignore
        value_list = [val for val in value_list if str(val) not in filter_list]
    return value_list


def filter_parameter(
    values: Mapping[str, List], filter: Optional[Mapping[str, Any]]
) -> Mapping[str, List]:

    if filter is None:
        return values

    filter_params = [param for param in filter.keys() if not param == "file"]
    for filt in filter_params:
        if filt not in values.keys():
            print(
                f"WARNING: Could not find {filt} in the specified parameter space: {values.keys()}.\n"
                f"No filter is going to be applied on {filt}."
            )
            continue
        values[filt] = apply_filter(values[filt], filter[filt])  # type: ignore
    return values


def get_all_parameter_combinations(
    values: Mapping[str, List]
) -> List[Mapping[str, str]]:
    comb_list: List = []
    all_combinations = []
    if not isinstance(values, type(None)):
        all_combinations = list(itertools.product(*values.values()))
    for comb in all_combinations:
        comb_dict = dict(zip(list(values.keys()), comb))
        comb_list.append(comb_dict)
    return comb_list


def dict_values_to_str(convert_dict: Mapping) -> Mapping:
    return {str(key): str(value) for key, value in convert_dict.items()}


def filter_parameter_combinations(  # type: ignore
    combinations: List[Mapping[str, str]], filter: Optional[Mapping[str, Any]]
) -> List[Mapping[str, str]]:

    if filter is None:
        return combinations
    if "file" not in filter.keys():
        return combinations
    with open(filter["file"]) as f:
        filter_json = json.load(f)
    filter_list = [
        dict_values_to_str(filt) for filt in filter_json["filter_combinations"]
    ]

    return [
        comb for comb in combinations if dict_values_to_str(comb) not in filter_list
    ]
