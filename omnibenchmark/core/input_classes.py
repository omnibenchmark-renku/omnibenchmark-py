from typing import TypeVar, Mapping, List, TypedDict, Optional
from pathlib import Path

from omnibenchmark.utils.user_input_checks import (
    check_name_matching,
    flatten,
    mixed_flatten,
    check_default_parameter,
    elements_to_list,
)
from omnibenchmark.utils.auto_input import (
    get_input_files_from_prefix,
    get_parameter_from_dataset,
    drop_none_elements,
)
from omnibenchmark.utils.exceptions import InputError
from omnibenchmark.management.data_commands import update_datasets_by_keyword
from omnibenchmark.management.parameter_checks import (
    filter_parameter,
    get_all_parameter_combinations,
    filter_parameter_combinations,
)

PathLike = TypeVar("PathLike", str, Path, None)


class OmniInput:
    """Class to store metadata of datasets and files that are specified as inputs in an omnibenchmark project"""

    def __init__(
        self,
        names: List[str],
        prefix: Optional[Mapping[str, List[str]]] = None,
        input_files: Optional[Mapping[str, Mapping[str, str]]] = None,
        keyword: Optional[List[str]] = None,
        default: Optional[str] = None,
        filter_names: Optional[List[str]] = None,
        filter_duplicated: bool = True,
        multi_data_matching: bool = False,
    ):
        """Class to manage inputs of an omnibenchmark

        Args:
            names (List[str]): Names of the input filetypes
            prefix (Optional[Mapping[str, List[str]]], optional): Substrings of the input filetypes. Defaults to None.
            input_files (Optional[Mapping[str, Mapping[str, str]]], optional): Input files ordered by file types.
                                                                               Defaults to None.
            keyword (Optional[List[str]], optional): Keyword to define which datasets are imported as input datasets.
                                                     Defaults to None.
            default (Optional[str], optional): Default input name (e.g., dataset). Defaults to None.
            filter_names (Optional[List[str]], optional): Input dataset names to be ignored. Defaults to None.
        """
        self.names = names
        self.prefix = prefix
        self.input_files = input_files
        self.keyword = keyword
        self.default = default
        self.filter_names = filter_names
        self.filter_duplicated = filter_duplicated
        self.multi_data_matching = multi_data_matching

        if self.input_files is None:

            if self.prefix is None or self.keyword is None:
                raise InputError(
                    "Missing input file definition. \n"
                    "Please specify explicit input files or \n"
                    "define prefixes AND dataset keyword(s)to automatically identify them."
                )

            check_name_matching(self.names, self.prefix.keys())
            self.input_files = get_input_files_from_prefix(
                self.prefix,
                self.keyword,
                self.filter_names,
                filter_duplicated=self.filter_duplicated,
                multi_data_matching=multi_data_matching,
            )

        if len(self.input_files) < 1:
            self.input_files = None
            print(
                f"WARNING: No input files in the current project detected.\n"
                f"Run OmniObject.update_object() to update and import input datasets.\n"
                f"Otherwise check the specified prefixes: {self.prefix}"
            )

        if self.input_files is not None:
            check_name_matching(
                self.names, flatten([pre.keys() for pre in self.input_files.values()])
            )

            if self.default is None:
                self.default = next(iter(self.input_files.items()))[0]

            if self.default not in self.input_files.keys():
                raise InputError(
                    f"Input default {self.default} not found. Must have corresponding input files."
                )

            self.default_files = self.input_files[self.default]

    def update_inputs(
        self,
        orchestrator: str,
        query_url: str,
        data_url: str,
        gitlab_url: str,
        check_o_url: bool = True,
        n_latest: int = 9,
        all: bool = True,
    ):
        """Update datasets and files that belong to this OmniInput object.
           This will also import new Datasets with the specified keyword..

        Args:
            orchestrator (str):  Orchestrator url that links all valid projects.
            query_url (str): URL to the knowledgebase dataset query API.
            data_url (str): URL to the knowledgebase dataset API.
            gitlab_url (str): General Gitlab url.
        """
        if self.keyword is not None:
            for key in self.keyword:
                update_datasets_by_keyword(
                    keyword=key,
                    filter_names=self.filter_names,
                    o_url=orchestrator,
                    query_url=query_url,
                    data_url=data_url,
                    gitlab_url=gitlab_url,
                    check_o_url=check_o_url,
                    n_latest=n_latest,
                    all=all,
                )
            if self.prefix is not None:
                check_name_matching(self.names, self.prefix.keys())
                self.input_files = get_input_files_from_prefix(
                    self.prefix,
                    self.keyword,
                    self.filter_names,
                    filter_duplicated=self.filter_duplicated,
                    multi_data_matching=self.multi_data_matching,
                )
                check_name_matching(
                    self.names,
                    flatten([pre.keys() for pre in self.input_files.values()]),
                )
            if self.input_files is not None and len(self.input_files) > 0:
                if self.default is None or self.default not in self.input_files.keys():
                    self.default = next(iter(self.input_files.items()))[0]


class OmniParameter:
    """Class to store metadata of datasets and files that are specified as parameter in an omnibenchmark project"""

    def __init__(
        self,
        names: List[str],
        values: Optional[Mapping[str, List]] = None,
        default: Optional[Mapping[str, str]] = None,
        keyword: Optional[List[str]] = None,
        filter: Optional[Mapping[str, str]] = None,
        combinations: Optional[List[Mapping[str, str]]] = None,
    ):
        """Initiate an instance of the class OmniParameter

        Args:
            names (List[str]): Name of all valid parameter
            values (Optional[Mapping[str, List]], optional): Parameter values, automatically detected from parameter dataset.
                                                             Defaults to None.
            default (Optional[Mapping[str, str]], optional): Default parameter values. Defaults to None.
            keyword (Optional[List[str]], optional): Keyword to import the parameter dataset with. Defaults to None.
            filter (Optional[Mapping[str, str]], optional): Filter to use for the parameter space. Defaults to None.
            combinations (Optional[List[Mapping[str, str]]], optional): All possible parameter combinations. Defaults to None.
        """
        self.names = names
        self.values = values
        self.default = default
        self.keyword = keyword
        self.filter = filter
        self.combinations = combinations

        if self.values is None and self.keyword is not None:
            self.values = get_parameter_from_dataset(self.names, self.keyword)

        if self.values is not None:
            check_name_matching(self.names, self.values.keys())
            self.values = elements_to_list(self.values)
            self.values = filter_parameter(self.values, self.filter)

            if self.combinations is None:
                self.combinations = get_all_parameter_combinations(self.values)

        if self.combinations is not None and len(self.combinations) > 0:
            check_name_matching(
                self.names, flatten([comb.keys() for comb in self.combinations])
            )
            self.combinations = filter_parameter_combinations(
                self.combinations, self.filter
            )
            if self.default is None or len(self.default) == 0:
                self.default = self.combinations[0]

        self.default = check_default_parameter(self.default, self.combinations)

    def update_parameter(
        self,
        orchestrator: str,
        query_url: str,
        data_url: str,
        gitlab_url: str,
        check_o_url: bool = True,
        n_latest: int = 9,
    ):
        """Update datasets and files that belong to this OmniParameter object.
           This will also import new Datasets with the specified keyword.
        Args:
            orchestrator (str): Orchestrator url that links all valid projects.
            query_url (str): URL to the knowledgebase dataset query API.
            data_url (str): URL to the knowledgebase dataset API.
            gitlab_url (str): General Gitlab url.
            check_o_url (bool): If inclusion to an orchestrator should be checked.
        """
        if self.keyword is not None:
            for key in self.keyword:
                update_datasets_by_keyword(
                    keyword=key,
                    o_url=orchestrator,
                    query_url=query_url,
                    data_url=data_url,
                    gitlab_url=gitlab_url,
                    check_o_url=check_o_url,
                    n_latest=n_latest,
                )
            if self.values is None:
                self.values = {}
            val = get_parameter_from_dataset(self.names, self.keyword)
            self.values = {
                x: mixed_flatten(drop_none_elements([val.get(x), self.values.get(x)]))
                for x in set(self.values).union(val)
            }
            self.values = elements_to_list(self.values)
            check_name_matching(self.names, self.values.keys())
            self.values = filter_parameter(self.values, self.filter)
            self.combinations = get_all_parameter_combinations(self.values)

            if self.combinations is not None:
                check_name_matching(
                    self.names, flatten([comb.keys() for comb in self.combinations])
                )
                self.combinations = filter_parameter_combinations(
                    self.combinations, self.filter
                )
                if self.default is None or len(self.default) == 0:
                    self.default = self.combinations[0]

            self.default = check_default_parameter(self.default, self.combinations)


class OutMapping(TypedDict):
    output_files: Optional[Mapping]
    input_files: Optional[Mapping]
    parameter: Optional[Mapping]
