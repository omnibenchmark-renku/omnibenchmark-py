"""Functions to facilitate automatic input generation from file/object, usually config.yaml"""

from typing import Dict, Mapping, List
from omnibenchmark.utils.exceptions import ParameterError
from renku.ui.api.models.dataset import Dataset
from difflib import SequenceMatcher
import re
import os
import json

def match_files_by_name(file_type_dict: Mapping[str, List[str]]) -> Mapping[str, Mapping]:
    match_dict: Dict = {}
    fi_types = list(file_type_dict.keys())
    fi_start = fi_types[0]
    fil_types = [fi_type for fi_type in fi_types if not fi_type == fi_start]
    for fi_idx, fi in enumerate(file_type_dict[fi_start]):
        group_nam = "inst" + str(fi_idx)
        match_dict[group_nam] = {fi_start: fi}
        for fi_type in fil_types:
            fi_top = ""
            seq_top = 0.0
            for fi_path in file_type_dict[fi_type]:
                fi_name = os.path.basename(fi_path)
                seq_match = SequenceMatcher(None, os.path.basename(fi), fi_name).ratio()
                if seq_match > seq_top:
                    seq_top = seq_match
                    fi_top = fi_path
            match_dict[group_nam][fi_type] = fi_top
    return(match_dict)


def get_input_files_from_prefix(
    input_prefix: Mapping[str, List[str]], keyword: List[str]
) -> Mapping[str, Mapping]:
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
                [prefixes] if not isinstance(prefixes, list) else prefixes        #type: ignore
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
            print(
                    f"WARNING: Ambigous input files. Found {in_file} for prefix {prefixes}.\n"
                    f"Automatic group detection for files in {data.name}.\n"
                    f"Please check matches to ensure correct groups: {group_dict}"
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

    print(f"The following datasets are specified as inputs: {input_files.keys()}")
    return input_files


def get_parameter_from_dataset(
    names: List[str], keyword: List[str]
) -> Mapping[str, List]:
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
