"""Functions to facilitate automatic input generation from file/object, usually config.yaml"""

from typing import Dict, Mapping, List, Optional, Union
from omnibenchmark.utils.exceptions import ParameterError
from collections import defaultdict
from renku.ui.api.models.dataset import Dataset
from omnibenchmark.renku_commands import renku_api
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
    len_s = len(s)
    res = ""
    for i in range(len_s):
        for j in range(i + 1, len_s + 1):

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


def get_name_hash_from_input_dict(infile_dict: Mapping[str, str]) -> str:
    """Get  the md5 hash of the joined values of a dictionary (e.g. of all input file names in an input file dict)

    Args:
        infile_dict (Mapping[str,str]): A dictionary with file types as key and file names as values.

    Returns:
        (str): The md5 hash of the concatenated file names
    """
    in_string = "".join(sorted(list(infile_dict.values())))
    hash_object = hashlib.md5(in_string.encode())
    return hash_object.hexdigest()


def into_list(obj: Union[str, list]) -> list:
    if not isinstance(obj, list):
        obj = [obj]
    return obj


def match_files_by_name(file_type_dict_all: Mapping) -> Mapping[str, Mapping]:
    """Find corresponding files by best matching names

    Args:
        file_type_dict (Mapping[str, List[str]]): Dictionary specifying all file types and their corresponding files

    Returns:
        Mapping[str, Mapping]: Mapping of best matches for all files between file types.
    """
    match_dict: Dict = {}
    file_type_dict = {
        fi_it: into_list(fi_val) for fi_it, fi_val in file_type_dict_all.items()
    }
    fi_types = list(file_type_dict.keys())
    fi_start = max(file_type_dict, key=lambda x: len(set(file_type_dict[x])))
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
            seq_top = 0
            for fi_path in fi_path_list:  # type:ignore
                fi_name = os.path.basename(fi_path)
                seq_match = (
                    SequenceMatcher(None, os.path.basename(fi), fi_name)  # type:ignore
                    .find_longest_match()
                    .size
                )
                if seq_match > seq_top:
                    seq_top = seq_match
                    top_blocks = SequenceMatcher(
                        None, os.path.basename(fi), fi_name
                    ).get_matching_blocks()
                    fi_top = fi_path
                elif seq_match == seq_top:
                    seq_blocks = SequenceMatcher(
                        None, os.path.basename(fi), fi_name
                    ).get_matching_blocks()
                    for seq, top in zip(seq_blocks, top_blocks):
                        if seq.size > top.size:
                            fi_top = fi_path
                            top_blocks = seq_blocks
                            break
                        if top.size > seq.size:
                            break
            match_dict[group_nam][fi_type] = fi_top
    com_dict = {
        get_name_hash_from_input_dict(match_dict[m_key])[0:5]
        + "_"
        + best_match_name_seq(match_dict[m_key]): match_dict[m_key]
        for m_key in match_dict.keys()
    }
    return com_dict


def check_dataset_name(input_dict: Mapping[str, str], data_name: str) -> str:
    """Check if data_name includes the longest matching sequence of all input files

    Args:
        input_dict (Mapping[str, str]): An input file type- name mapping
        data_name (str): Dataset name to check

    Returns:
        str: Either the dataset name, if it is equal the longest matching sequence
             or a name of the dataset name, longest match seq and an input file name hash.
    """
    best_match = best_match_name_seq(input_dict)
    if best_match == data_name:
        return data_name
    else:
        new_name = (
            data_name
            + "_"
            + get_name_hash_from_input_dict(input_dict)[0:5]
            + "_"
            + best_match
        )
        return new_name.rstrip("_- .")


def remove_duplicated_inputs(pat_list: List, in_files: List[str]) -> List[str]:
    """Removes elements from input files if their names are identical except for the file prefix pattern
       when these pattern are associated with the same input file type. Will automatically select the first match.

    Args:
        pat_list (List): List of file prefix pattern generated by re.compile
        in_files (List[str]): All input files that matched one of the pattern in pat_list

    Returns:
        List[str]: input file list with duplicated files removed.
    """
    simp_infiles = in_files
    for pat in pat_list:
        simp_infiles = [re.sub(pat, "", s) for s in simp_infiles]
    stem_ind = defaultdict(list)
    for i, stem in enumerate(simp_infiles):
        stem_ind[stem].append(i)
    ind_keep = [ind[0] for ind in stem_ind.values()]
    return [in_files[ind] for ind in ind_keep]


def match_input_pattern(
    input_files: Dict,
    input_prefix: Mapping,
    name: str,
    files: List,
    filter_duplicated: bool = True,
) -> Dict:
    """Match files specified in files by input_prefix into best matching groups. Append results to the input_files dictionary.

    Args:
        input_files (Dict): Dictionary with all already assigned inputs.
        input_prefix (Mapping): Prefix name - prefix value mapping.
        name (str): input name to be used as key in input_files.
        files (List): List of all files to be grouped.
        filter_duplicated (bool, optional): If duplicated inputs groups should be rautomnatically removed. Defaults to True.

    Returns:
        Dict: Dictionary specified in input_files with the new best matching groups added.
    """
    tmp_dict: Dict = {}
    input_files[name] = {}
    for file_type, prefixes in input_prefix.items():
        prefix_list = (
            [prefixes] if not isinstance(prefixes, list) else prefixes  # type: ignore
        )
        pat_list = [re.compile(pattern) for pattern in prefix_list]
        in_file = [
            fi.path
            for fi in files
            if any(pattern.search(os.path.basename(fi.path)) for pattern in pat_list)
        ]
        if len(in_file) > 1:
            if len(pat_list) > 1 and filter_duplicated:
                in_file = remove_duplicated_inputs(pat_list=pat_list, in_files=in_file)
            tmp_dict[file_type] = in_file
        elif len(in_file) < 1:
            print(
                f"WARNING:Could not find any input file matching the following pattern {prefixes}.\n"
                f"Please make sure you specified a correct prefix! \n"
                f"Input dataset {name} will be ignored!"
            )
            break
        else:
            input_files[name][file_type] = in_file[0]
    if len(tmp_dict) > 0:
        tmp_dict.update(input_files[name])
        group_dict = match_files_by_name(tmp_dict)
        n = len(in_file) if len(in_file) <= 5 else 5
        print(
            f"WARNING: Ambigous input files. Found {in_file[0:n]}, ...\n"
            f"Automatic group detection for files in {name}.\n"
            f"Please check matches to ensure correct groups: 'omni_obj.inputs.input_files'"
        )
        del input_files[name]
        group_data_dict = {name + "_" + k: group_dict[k] for k in group_dict.keys()}
        input_files.update(group_data_dict)
    return input_files


def get_input_files_from_prefix(
    input_prefix: Mapping[str, List[str]],
    keyword: List[str],
    filter_names: Optional[List[str]] = None,
    filter_duplicated: bool = True,
    multi_data_matching: bool = False,
) -> Mapping[str, Mapping]:
    """Find input files by prefix

    Args:
        input_prefix (Mapping[str, List[str]]): Dictionary with all file types and their valid prefixes.
        keyword (List[str]): Keyword of datasets that contain input files
        filter_names (Optional[List[str]]): Dataset names to be ignored when querying input files
        filter_duplicated (bool): If duplicated inputs from the same dataset and prefix pattern
                                  associated to the same input file types shall automatically be removed.
        multi_data_matching (bool): If true files from different renku datasets will be matched (defaults to False).

    Returns:
        Mapping[str, Mapping]: Input file types with their corresponding files.
    """
    input_files: Dict = {}
    # datasets = Dataset.list()
    datasets = renku_api.renku_dataset_list()
    key_data = [
        dataset
        for dataset in datasets
        if any(key in keyword for key in dataset.keywords)
    ]
    if multi_data_matching:
        all_fi = [data.files for data in key_data]
        all_files = [item for sublist in all_fi for item in sublist]
        input_files = match_input_pattern(
            input_files=input_files,
            input_prefix=input_prefix,
            name="all",
            files=all_files,
            filter_duplicated=filter_duplicated,
        )
    else:
        for data in key_data:
            input_files = match_input_pattern(
                input_files=input_files,
                input_prefix=input_prefix,
                name=data.name,
                files=data.files,
                filter_duplicated=filter_duplicated,
            )
    file_types = input_prefix.keys()

    # Filter incomplete, non existing and explicitly filtered data
    incomplete_data = [
        data
        for data in input_files.keys()
        if not all(fi_type in input_files[data].keys() for fi_type in file_types)
    ]
    non_exist_data = [
        data
        for data in input_files.keys()
        if not all(os.path.exists(fi) for fi in input_files[data].values())
    ]
    rm_data = incomplete_data + non_exist_data
    if filter_names is not None:
        filter_list = [
            filter_nam
            for filter_nam in filter_names
            if filter_nam in input_files.keys()
        ]
        rm_data = rm_data + filter_list
    for data in rm_data:
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
    datasets = renku_api.renku_dataset_list()
    # datasets = Dataset.list()
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


def drop_none_elements(l: List):
    return [element for element in l if element is not None]
