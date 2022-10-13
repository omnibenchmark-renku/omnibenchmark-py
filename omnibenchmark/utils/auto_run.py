""" All functions around automatization of runs/activities and updates of those"""
from typing import Iterable, Mapping, List, Optional, Union, Dict
from renku.domain_model.workflow.plan import Plan
from omnibenchmark.core.input_classes import OutMapping
from collections import defaultdict
from renku.core.util.urls import get_slug
from omnibenchmark.utils.user_input_checks import flatten
from os import PathLike


def map_plan_names(plan: Plan) -> Mapping[str, str]:
    """Get default inputs/parameter/outputs from a plan

    Args:
        plan (Plan): A renku plan

    Returns:
        Mapping[str, str]: A mapping of defaults secified by the renku plan
    """
    plan_map = {}
    for input in plan.inputs:
        plan_map[input.name] = input.default_value
    for output in plan.outputs:
        plan_map[output.name] = output.default_value
    for parameter in plan.parameters:
        plan_map[parameter.name] = parameter.default_value

    return plan_map


def get_file_type_dict(file_mapping: OutMapping) -> Mapping[str, str]:
    """Get a dictionary of file names and file types with types as keys.

    Args:
        file_mapping (OutMapping): An OutMapping

    Returns:
        Mapping[str, str]: A mapping of file types (keys) and their file names (values)
    """
    type_map: Dict = {}
    for file_dict in list(file_mapping.values()):
        if file_dict is not None:
            for file_type, file_name in file_dict.items():  # type: ignore
                type_map[str(file_type)] = file_name
    return type_map


def get_file_name_dict(
    file_mapping: List[Mapping[str, Optional[str]]]
) -> Mapping[str, str]:
    """Get a dictionary of file names and file types with names as keys.

    Args:
        file_mapping (List[Mapping[str, Optional[str]]]): A List of OutMappings

    Returns:
        Mapping[str, str]: A mapping of file names (keys) and their file types (values)
    """
    map_dict: Dict = defaultdict(list)
    for mapping in file_mapping:
        joined_dict = {
            str(file_name): file_type for file_type, file_name in mapping.items()
        }
        map_dict.update(joined_dict)
    return map_dict


def map_plan_names_by_prefix(
    plan: Plan, plan_dict: Mapping[str, str]
) -> Dict[str, str]:
    """Get a mapping of plan names from the specified prefixes

    Args:
        plan (Plan): A renku plan.
        plan_dict (Mapping[str, str].): A dictionary of all possible inputs/parameter/outputs.

    Returns:
        Dict[str, str]: A mapping of plan names and file types
    """
    map_dict: Dict = {}
    rev_dict: Dict = {}
    for key, value in plan_dict.items():
        rev_dict.setdefault(value, set()).add(key)

    non_unique = flatten([val for val in rev_dict.values() if len(val) > 1])
    plan_elements = [
        item
        for sublist in [plan.inputs, plan.outputs, plan.parameters]
        for item in sublist
    ]

    for plan_name in non_unique:
        plan_element = [
            plan_ele for plan_ele in plan_elements if plan_ele.name == plan_name
        ]
        if len(plan_element) == 1 and not isinstance(
            plan_element[0].prefix, type(None)
        ):
            file_type = get_slug(
                plan_element[0].prefix.strip(" -="), invalid_chars=["."]
            )
            map_dict[file_type] = plan_name
    return map_dict


def map_plan_names_file_types(
    plan: Plan, file_dict: Mapping[str, str]
) -> Mapping[str, str]:
    """Get a mapping of plan names and file types from an existing plan.

    Args:
        plan (Plan): A ren,u plan
        file_dict (Mapping[str, str]): A mapping of file types and names

    Returns:
        Mapping[str, str]: A mapping of plan names and file types
    """
    plan_dict = map_plan_names(plan)
    map_dict = map_plan_names_by_prefix(plan, plan_dict)
    for plan_name, plan_element in plan_dict.items():
        file_type = file_dict[str(plan_element)]
        if len(file_type) > 0 and file_type not in map_dict:
            map_dict[file_type] = plan_name
    return map_dict


def get_file_mapping_from_out_files(
    out_files: List[Union[PathLike, str, None]],
    file_mapping: Optional[List[OutMapping]] = None,
) -> List[OutMapping]:
    """Get the OutMapping from the output file names

    Args:
        out_files (List[Union[PathLike, str, None]]): A list of  output file names
        file_mapping (Optional[List[OutMapping]]): A List of OutMappings.

    Returns:
        List[OutMapping]: A List of OutMappings.
    """
    try:
        map_list = [
            mapping
            for mapping in file_mapping  # type:ignore
            if any(
                out_file in out_files
                for out_file in list(mapping["output_files"].values())  # type:ignore
            )
        ]
    except:
        map_list = []
    finally:
        return map_list


def get_file_list_from_out_mapping(
    out_mapping: List[OutMapping],
) -> Optional[List[str]]:
    """Get a list of all files from a list of OutMappings

    Args:
        out_mapping (List[OutMapping]): A List of OutMappings

    Returns:
        Optional[List[str]]: A List of all files.
    """
    all_files = []
    for mapping in out_mapping:
        try:
            file_list: Iterable = [
                file_path
                for file_dict in mapping.values()
                for file_path in file_dict.values()  # type:ignore
            ]
        except:
            file_list: Iterable = []  # type:ignore
        finally:
            all_files.append(file_list)
    return flatten(all_files)
