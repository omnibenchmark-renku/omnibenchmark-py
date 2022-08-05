"""Functions to facilitate automatic input generation from file/object, usually config.yaml"""

from typing import Dict, Mapping, List
from omnibenchmark.utils.exceptions import ParameterError
from renku.ui.api.models.dataset import Dataset
from difflib import SequenceMatcher
import re
import os
import json


def find_stem(arr):
    """Find a common substring from a list of strings

    Args:
        arr (Array): Array of strings

    Returns:
        str: longest common substring
    """
    n = len(arr)
    # Take first word from array
    # as reference
    s = arr[0]
    l = len(s)
    res = ""
    for i in range(l):
        for j in range(i + 1, l + 1):

            # generating all possible substrings
            # of our reference string arr[0] i.e s
            stem = s[i:j]
            k = 1
            for k in range(1, n):

                # Check if the generated stem is
                # common to all words
                if stem not in arr[k]:
                    break

            # If current substring is present in
            # all strings and its length is greater
            # than current result
            if k + 1 == n and len(res) < len(stem):
                res = stem

    return res


def best_match_name_seq(map_dict: Mapping[str, str]) -> str:
    """Get the longest common substring from a mapping of file names without directories

    Args:
        map_dict (Mapping[str, str]): Mapping of file names

    Returns:
        str: Longest common substring
    """
    na_list = [os.path.basename(fi_nam) for fi_nam in map_dict.values()]
    nam_list = [os.path.splitext(nam)[0] for nam in na_list]
    name_list = [os.path.splitext(nam)[0] for nam in nam_list]
    com_sub = find_stem(name_list)
    return com_sub


def match_files_by_name(
    file_type_dict: Mapping[str, List[str]]
) -> Mapping[str, Mapping]:
    """Find corresponding files by best matching names

    Args:
        file_type_dict (Mapping[str, List[str]]): Dictionary specifying all file types and their corresponding files

    Returns:
        Mapping[str, Mapping]: Mapping of best matches for all files between file types.
    """
    match_dict: Dict = {}
    fi_types = list(file_type_dict.keys())
    fi_start = fi_types[0]
    fil_types = [fi_type for fi_type in fi_types if not fi_type == fi_start]
    for fi_idx, fi in enumerate(file_type_dict[fi_start]):
        group_nam = "inst" + str(fi_idx)
        match_dict[group_nam] = {fi_start: fi}
        for fi_type in fil_types:
            fi_path_list = (
                [file_type_dict[fi_type]]
                if not isinstance(file_type_dict[fi_type], list)
                else file_type_dict[fi_type]
            )
            fi_top = ""
            seq_top = 0.0
            for fi_path in fi_path_list:  # type:ignore
                fi_name = os.path.basename(fi_path)
                seq_match = SequenceMatcher(None, os.path.basename(fi), fi_name).ratio()
                if seq_match > seq_top:
                    seq_top = seq_match
                    fi_top = fi_path
            match_dict[group_nam][fi_type] = fi_top
    com_dict = {
        m_key + "_" + best_match_name_seq(match_dict[m_key]): match_dict[m_key]
        for m_key in match_dict.keys()
    }
    return com_dict


def get_input_files_from_prefix(
    input_prefix: Mapping[str, List[str]], keyword: List[str]
) -> Mapping[str, Mapping]:
    """Find input files by prefix

    Args:
        input_prefix (Mapping[str, List[str]]): Dictionary with all file types and their valid prefixes.
        keyword (List[str]): Keyword of datasets that contain input files

    Returns:
        Mapping[str, Mapping]: Input file types with their corresponding files.
    """
    input_files: Dict = {}
    datasets = Dataset.list()
    key_data = [
        dataset
        for dataset in datasets
        if any(key in keyword for key in dataset.keywords)
    ]
    for data in key_data:
        tmp_dict: Dict = {}
        input_files[data.name] = {}
        for file_type, prefixes in input_prefix.items():
            prefix_list = (
                [prefixes]                              # type: ignore
                if not isinstance(prefixes, list)
                else prefixes  
            )
            pat_list = [re.compile(pattern) for pattern in prefix_list]
            in_file = [
                fi.path
                for fi in data.files
                if any(
                    pattern.search(os.path.basename(fi.path)) for pattern in pat_list
                )
            ]
            if len(in_file) > 1:
                tmp_dict[file_type] = in_file
            elif len(in_file) < 1:
                print(
                    f"WARNING:Could not find any input file matching the following pattern {prefixes}.\n"
                    f"Please make sure you specified a correct prefix! \n"
                    f"Input dataset {data.name} will be ignored!"
                )
                break
            else:
                input_files[data.name][file_type] = in_file[0]
        if len(tmp_dict) > 0:
            tmp_dict.update(input_files[data.name])
            group_dict = match_files_by_name(tmp_dict)
            n = len(in_file) if len(in_file) <= 5 else 5
            print(
                f"WARNING: Ambigous input files. Found {in_file[0:n]}, ...\n"
                f"Automatic group detection for files in {data.name}.\n"
                f"Please check matches to ensure correct groups: 'omni_obj.inputs.input_files'"
            )
            del input_files[data.name]
            input_files.update(group_dict)
    file_types = input_prefix.keys()
    incomplete_data = [
        data
        for data in input_files.keys()
        if not all(fi_type in input_files[data].keys() for fi_type in file_types)
    ]
    for data in incomplete_data:
        del input_files[data]

    return input_files


def get_parameter_from_dataset(
    names: List[str], keyword: List[str]
) -> Mapping[str, List]:
    """Get parameter from a renku dataset

    Args:
        names (List[str]): Parameter names
        keyword (List[str]): Keyword of the parameter dataset.

    Raises:
        ParameterError: _description_

    Returns:
        Mapping[str, List]: Mapping with parameters and all possible values
    """
    values: Dict = {}
    datasets = Dataset.list()
    key_data = [
        dataset
        for dataset in datasets
        if any(key in keyword for key in dataset.keywords)
    ]
    for data in key_data:
        if not len(data.files) == 1:
            raise ParameterError(
                f"Could not identify parameter json file."
                f"Please check the specified keyword {keyword} and dataset {data}."
            )
        param_file = data.files[0]
        with open(param_file.path) as f:
            param_json = json.load(f)

        for nam in names:
            if nam not in param_json.keys():
                print(
                    f"WARNING: Could not find a matching parameter for {nam}.\n"
                    f"The following parameter exist in {data}: {param_json.keys()} \n"
                    f"Please post an issue to request missing parameter."
                )
                continue
            values[nam] = param_json[nam]

    print(f"The following parameter are used: {values.keys()}")
    return values
