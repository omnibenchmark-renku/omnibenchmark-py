"""Functions to facilitate automatic input generation from file/object, usually config.yaml"""

from typing import Dict, Mapping, List, Optional
from omnibenchmark.utils.exceptions import ParameterError
from renku.ui.api.models.dataset import Dataset
from difflib import SequenceMatcher
import hashlib
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
    return com_sub.rstrip("_- .")

def get_name_hash_from_input_dict(infile_dict: Mapping[str,str]) -> str:
    """Get  the md5 hash of the joined values of a dictionary (e.g. of all input file names in an input file dict) 

    Args:
        infile_dict (Mapping[str,str]): A dictionary with file types as key and file names as values.

    Returns:
        (str): The md5 hash of the concatenated file names
    """
    in_string = "".join(list(infile_dict.values()))
    hash_object = hashlib.md5(in_string.encode())
    return hash_object.hexdigest()


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
    fi_start = max(file_type_dict, key= lambda x: len(set(file_type_dict[x])))
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
        get_name_hash_from_input_dict(match_dict[m_key])[0:5] + "_" + best_match_name_seq(match_dict[m_key]): match_dict[m_key]
        for m_key in match_dict.keys()
    }
    return com_dict

def check_dataset_name(input_dict: Mapping[str, str], data_name: str) -> str:
    """Check if data_name includes the longest matching sequence of all input files

    Args:
        input_dict (Mapping[str, str]): An input file type- name mapping
        data_name (str): Dataset name to check

    Returns:
        str: Either the dataset name, if it is equal the longest matching sequence or a name of the dataset name, longest match seq and an input file name hash.
    """
    best_match = best_match_name_seq(input_dict)
    if best_match == data_name:
        return data_name
    else:
        new_name = data_name + "_" + get_name_hash_from_input_dict(input_dict)[0:5] + "_" + best_match
        return new_name.rstrip("_- .")

def get_input_files_from_prefix(
    input_prefix: Mapping[str, List[str]], keyword: List[str], filter_names: Optional[List[str]] = None
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
                [prefixes]  # type: ignore
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
            group_data_dict = {data.name + "_" + k: group_dict[k] for k in group_dict.keys()}
            input_files.update(group_data_dict)
    file_types = input_prefix.keys()
    incomplete_data = [
        data
        for data in input_files.keys()
        if not all(fi_type in input_files[data].keys() for fi_type in file_types)
    ]
    if filter_names is not None:
        filter_list = [filter_nam for filter_nam in filter_names if filter_nam in input_files.keys()]
        incomplete_data = incomplete_data + filter_list
    for data in incomplete_data:
        del input_files[data]
    dataset_names = [data.name for data in key_data]

    for input_nam in list(input_files.keys()):
        if input_nam in dataset_names:
            new_name = check_dataset_name(input_files[input_nam], input_nam)
            if new_name != input_nam:
                input_files[new_name] = input_files[input_nam]
                del input_files[input_nam]

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
