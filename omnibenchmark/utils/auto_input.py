"""Functions to facilitate automatic input generation from file/object, usually config.yaml"""

from typing import Dict, Mapping, List
from omnibenchmark.utils.exceptions import ParameterError
from renku.ui.api.models.dataset import Dataset
import re
import os
import json


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
        input_files[data.name] = {}
        for file_type, prefixes in input_prefix.items():
            prefixes = [prefixes] if not isinstance(prefixes, list) else prefixes                     # type: ignore
            pat_list = [re.compile(pattern) for pattern in prefixes]
            in_file = [
                fi.path
                for fi in data.files
                if any(pattern.search(os.path.basename(fi.path)) for pattern in pat_list)
            ]
            if len(in_file) > 1:
                print(
                    f"WARNING: Ambigous input files. Found {in_file} for prefix {prefixes}.\n"
                    f"Please make sure you specified a correct prefix! \n"
                    f"Input dataset {data} will be ignored!"
                )
                break
            elif len(in_file) < 1:
                print(
                    f"WARNING:Could not find any input file matching the following pattern {prefixes}.\n"
                    f"Please make sure you specified a correct prefix! \n"
                    f"Input dataset {data} will be ignored!"
                )
                break
            else:
                input_files[data.name][file_type] = in_file[0]

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
