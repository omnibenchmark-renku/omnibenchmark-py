"""Commands related to import and update relevant datasets"""
from typing import List, Mapping, Any, Optional, Tuple
from renku.api import Dataset
from omnibenchmark.renku_commands import renku_api
from omnibenchmark.renku_commands.datasets import (
    renku_dataset_import,
    renku_dataset_update,
    renku_add_to_dataset,
    renku_unlink_from_dataset,
    renku_dataset_remove,
)
from omnibenchmark.utils.exceptions import InputError
from omnibenchmark.utils.general import into_list
from omnibenchmark.management.data_checks import query_multipages
import requests
import re
import os
import urllib
import gitlab
from omnibenchmark.renku_commands.general import renku_save
from iteration_utilities import unique_everseen  # type: ignore


# Find datasets by string
def query_datasets_by_string(
    string: str,
    url: str = "https://renkulab.io/knowledge-graph/datasets?query=",
    page_item: int = 100,
) -> List[Mapping[Any, Any]]:
    """Query datasets in the knowledge base by a string.

    Args:
        string (str): String to query datasets for
        url (str): URL to the knowledgebase dataset query API. Default "https://renkulab.io/knowledge-graph/datasets?query=".

    Returns:
        List[Mapping[Any, Any]]: List of all datasets associated to that string with their metadata
    """
    query_url = url + string
    return query_multipages(url=query_url, page_item=page_item)


# Find dataset by match of property
def query_datasets_by_property(
    string: str,
    url: str = "https://renkulab.io/knowledge-graph/datasets?query=",
    match_string: Optional[str] = None,
    property_name: str = "keywords",
) -> List[Mapping[Any, Any]]:
    """Query datasets in a knowledge base by string and matching property.

    Args:
        string (str): String to query datasets for
        url (str): URL to the knowledgebase dataset query API. Default "https://renkulab.io/knowledge-graph/datasets?query=".
        match_string (Optional[str], optional): String to filter matching properties by.
                                                Will be the same as the query string, if None.
                                                Defaults to None.
        property_name (str, optional): Property to filter datasets by. Defaults to "keywords".

    Returns:
        List[Mapping[Any, Any]]: List of all datasets associated to that string
                                 with the property matching the "match_string" with their metadata.
    """
    if match_string is None:
        match_string = string
    all_data_json = query_datasets_by_string(string=string, url=url)
    matched_dataset: List = []
    for dataset in all_data_json:
        data_prop = (
            [dataset[property_name]]
            if not isinstance(dataset[property_name], list)
            else dataset[property_name]
        )
        if any(prop_val.lower() == match_string.lower() for prop_val in data_prop):
            matched_dataset.append(dataset)
    return matched_dataset


# Filter exisiting datasets
def filter_existing(data_json: List) -> Tuple[List, List]:
    """Split list of datasets into a list of thse that already exist in the project and those that do not exist by name.

    Args:
        data_json (List): List of datasets with their metadata mappings

    Returns:
        Tuple[List, List]: First List contains not existing datasets,
                           second list existing datasets in the current project
    """
    update_list: List = []
    import_list: List = []
    # datasets = Dataset.list()
    datasets = renku_api.renku_dataset_list()
    name_list = [dataset.name for dataset in datasets]
    for data in data_json:
        if data["name"] in name_list:
            update_list.append(data)
        else:
            import_list.append(data)
    return import_list, update_list


# Apply predefined filter
def import_filter(data_json: List, filter_names: Optional[List[str]] = None) -> List:
    """Filter import datasets by specified names.

    Args:
        data_json (List): List of datasets with their metadata mappings
        filter_names (Optional[List[str]], optional): Names to be filtered from the dataset list. Defaults to None.

    Returns:
        List: Filtered list of dataset metadata
    """
    if filter_names is None:
        return data_json
    else:
        return [data for data in data_json if data["name"] not in filter_names]


# Get dataset field by matching property
def get_field_by_dataset_property(
    string: str,
    url: str = "https://renkulab.io/knowledge-graph/datasets?query=",
    property_name: str = "keywords",
    field: str = "identifier",
    filter_ex: bool = False,
    filter_names: Optional[List[str]] = None,
) -> Tuple[List[str], List[str]]:
    """Get a specific field of all datasets that match a specified query.

    Args:
        string (str): String to query datasets for
        url (str, optional): URL to the knowledgebase dataset query API.
        property_name (str, optional): Dataset property to match with the query string. Defaults to "keywords".
        field (str, optional): Dataset field to return. Defaults to "identifier".
        filter_ex (bool, optional): If true return the name of all existing datasets instead. Defaults to False.
        filter_names (Optional[List[str]], optional): Names to be filtered from the dataset list. Defaults to None.

    Returns:
        Tuple[List[str], List[str]]: List with all or not already existing datasets.
                                     List with names of existing datasets.
    """
    data_json = query_datasets_by_property(
        string=string, url=url, property_name=property_name
    )
    data_json = import_filter(data_json=data_json, filter_names=filter_names)
    up_json: List = []
    if filter_ex:
        data_json, up_json = filter_existing(data_json=data_json)

    return (
        [dataset[field] for dataset in data_json],
        [dataset["name"] for dataset in up_json],
    )


# Get data info by dataset id
def get_data_info_by_id(
    id: str, url: str = "https://renkulab.io/knowledge-graph/datasets/"
) -> Mapping[Any, Any]:
    """Get dataset metadat by dataset id

    Args:
        id (str): Renku dataset identifier
        url (str, optional): URL to the knowledgebase dataset API. Defaults to "https://renkulab.io/knowledge-graph/datasets/".

    Returns:
        Mapping[Any, Any]: Dataset metadata (e.g., name, description, keywords, links, creator, ...)
    """
    query_url = url + id
    response = requests.get(query_url)
    return response.json()


def find_dataset_linked_to_wflow(
    info_list: List[Mapping], top: int = 2, filter_pat: str = "meta"
) -> List[Mapping]:
    """Check a list of datasets for workflows associated to their linked files.

    Args:
        info_list (List[Mapping]): List of datasets and their metadata to filter
        top (int, optional): Number of associated files to check for workflow association Defaults to 2.
        filter_pat (str, optional): Filter pattern to exclude files by. Defaults to "meta".

    Returns:
        List[Mapping]: List of datasets and metadata with files that have a workflow linked to them.
    """
    origin_info = []
    for info in info_list:
        data_files = info["hasPart"]
        data_file_list = [
            data_fi["atLocation"]
            for data_fi in data_files
            if filter_pat not in data_fi["atLocation"]
        ]
        for data_file in data_file_list[:top]:
            file_lineage = requests.get(
                info["project"]["_links"][0]["href"]
                + "/files/"
                + urllib.parse.quote(data_file, safe="")
                + "/lineage"
            )
            if "message" in file_lineage.json().keys():
                continue
            if "edges" in file_lineage.json().keys():
                if any(
                    data_file in fi["target"] for fi in file_lineage.json()["edges"]
                ):
                    if info not in origin_info:
                        origin_info.append(info)
    return origin_info


def filter_duplicated_names(info_list: List[Mapping]) -> List[Mapping]:
    """Filter a list of datasets to get only the original dataset if their are multiple datasets found with the same name.

    Args:
        info_list (List[Mapping]): List of datasets with metadata to filter

    Returns:
        List[Mapping]: Dataset list with unique datasets
    """
    info_list = list(unique_everseen(info_list))
    name_list = [info["name"] for info in info_list]
    dup_names = set(
        [info_name for info_name in name_list if name_list.count(info_name) > 1]
    )
    uni_list = [info for info in info_list if info["name"] not in dup_names]
    for dup in dup_names:
        dup_info = [info for info in info_list if info["name"] == dup]
        dup_project = set([info["project"]["_links"][0]["href"] for info in dup_info])
        if len(dup_project) == 1:
            all_datasets = query_multipages(url=list(dup_project)[0] + "/datasets")
            all_ids = [dat["identifier"] for dat in all_datasets]
            origin_info = [info for info in dup_info if info["identifier"] in all_ids]
        else:
            o_info = find_dataset_linked_to_wflow(dup_info)
            o_project = set([info["project"]["_links"][0]["href"] for info in o_info])
            if len(o_project) == 1:
                all_datasets = query_multipages(url=list(o_project)[0] + "/datasets")
                all_ids = [dat["identifier"] for dat in all_datasets]
                origin_info = [info for info in o_info if info["identifier"] in all_ids]
            else:
                origin_info = []
        if len(origin_info) != 1:
            print(
                f"WARNING: Could not identify origin of {dup}.\n"
                f"If you anyways want to use and import it, consider manual import:\n"
                f"renku dataset import DATA_URL"
            )
            continue
        uni_list.append(*origin_info)
    return uni_list


# Get origin dataset ids
def get_origin_dataset_ids(
    ids: List[str], url: str = "https://renkulab.io/knowledge-graph/datasets/"
) -> List[Mapping]:
    """Filter a list of dataset ids for original dataset ids
       (datasets associated to projects, where they were generated and not imported).

    Args:
        ids (List[str]): List of dataset ids to filter
        url (str, optional): URL to the knowledgebase dataset API. Defaults to "https://renkulab.io/knowledge-graph/datasets/".

    Returns:
        List[Mapping]: Filtered datasets and their metadata
    """
    all_infos: List = []
    for data_id in ids:
        data_info = get_data_info_by_id(id=data_id, url=url)
        if "sameAs" in data_info.keys():
            if not data_info["sameAs"] == data_info["url"]:
                same_id = data_info["sameAs"].split("/")[
                    -1
                ]  # Unstable string manipulation??
                data_info = get_data_info_by_id(id=same_id, url=url)
        if data_info not in all_infos and "name" in data_info.keys():
            all_infos.append(data_info)
    origin_infos = filter_duplicated_names(all_infos)
    return origin_infos


def get_project_info_from_url(project_url: str) -> Mapping[Any, Any]:
    """Get project metadata from url

    Args:
        project_url (str): URL to the knowledgebase dproject URL.

    Returns:
        Mapping[Any, Any]: Project metadata dictionary
    """
    response = requests.get(project_url)
    return response.json()


def check_orchestrator(
    data_info: Mapping,
    o_url: str,
    gitlab_url: str = "https://renkulab.io/gitlab",
    n_latest: int = 9,
) -> Optional[str]:
    """Check if a dataset is associated to a project that is part of the specified orchestrators projects.

    Args:
        data_info (Mapping): Dataset metadata to check
        o_url (str): orchestrator url to check if the dataset project is associated to.
        gitlab_url (url, optional): General Gitlab url. Defaults to "https://renkulab.io/gitlab".

    Returns:
        Optional[str]: Dataset url, if the dataset is associated to a project that is part of the orchestrator.
    """
    project_url = data_info["project"]["_links"][0]["href"]
    project_info = get_project_info_from_url(project_url)
    if "identifier" not in project_info.keys():
        print(
            f"Warning: Can't find dataset at {project_url}.\n"
            f"Please check {data_info['name']}.\n"
        )
        return None
    o_info = get_project_info_from_url(o_url)
    renku_git = gitlab.Gitlab(gitlab_url)
    o_git = renku_git.projects.get(o_info["identifier"])
    success = o_git.pipelines.list(status="success", all=False)
    latest = o_git.pipelines.list(order_by="updated_at", all=False)[
        :n_latest
    ]  # type:ignore
    query_pipes = list(set(success + latest))  # type:ignore
    bridge_projects: List = []
    for pipe in query_pipes:
        bridge_projects.extend(
            [
                brid.downstream_pipeline["project_id"]
                for brid in pipe.bridges.list()
                if brid.status == "success"
            ]
        )
        if project_info["identifier"] in bridge_projects:
            return data_info["url"]
    return None


def get_data_url_by_keyword(
    keyword: str,
    o_url: str,
    filter_ex: bool = False,
    filter_names: Optional[List[str]] = None,
    query_url: str = "https://renkulab.io/knowledge-graph/datasets?query=",
    data_url: str = "https://renkulab.io/knowledge-graph/datasets/",
    gitlab_url: str = "https://renkulab.io/gitlab",
    check_o_url: bool = True,
    n_latest: int = 9,
) -> Tuple[List[str], List[str]]:
    """Get all valid dataset urls by matching keywords.

    Args:
        keyword (str): keyword to find datasets by
        o_url (str): Orchestrator url that links all valid projects
        filter_ex (bool, optional): If existing datasets should be filtered automatically. Defaults to False.
        filter_names (Optional[List[str]], optional): Names to be filtered from the dataset list. Defaults to None.
        query_url (str, optional): URL to the knowledgebase dataset query API.
        data_url (str, optional): URL to the knowledgebase dataset API.
        gitlab_url (str, optional): General Gitlab url. Defaults to "https://renkulab.io/gitlab".

    Returns:
        Tuple[List[str], List[str]]: 1. List with all matching non-existing dataset urls,
                                     2. List with all matching existig dataset urls.
    """
    all_ids, up_exist = get_field_by_dataset_property(
        string=keyword, url=query_url, filter_ex=filter_ex, filter_names=filter_names
    )
    up_exist = list(unique_everseen(up_exist))
    if len(all_ids) + len(up_exist) < 1:
        print(f"WARNING:No datasets found with keyword {keyword}")
        return [], []
    origin_infos = get_origin_dataset_ids(ids=all_ids, url=data_url)
    if len(origin_infos) + len(up_exist) < 1:
        print(
            "WARNING:Could not identify dataset sources.\n"
            f"Please check each of {data_url}{all_ids} to make sure they are the intended source"
        )
        return [], []
    if check_o_url:
        omni_ids = [
            check_orchestrator(
                data_info=info, o_url=o_url, gitlab_url=gitlab_url, n_latest=n_latest
            )
            for info in origin_infos
        ]
    else:
        omni_ids = [data_info["url"] for data_info in origin_infos]
    omni_ids = list(filter(None, omni_ids))
    if len(omni_ids) < 1:
        if len(up_exist) < 1:
            print(
                f"WARNING:No dataset with keyword {keyword} was associated to an omnibenchmark at ${o_url}\n"
                f"Please check if you specified the correct benchmark/url \n"
            )
        else:
            print(f"No new dataset with keyword {keyword} was found.")
    return omni_ids, up_exist  # type:ignore


def find_datasets_with_non_matching_keywords(
    keywords: List[str], include: Optional[List[str]] = None, remove: bool = True
):
    """Find datasets with non matching keywords

    Args:
        keywords (List[str]): Keywords to keep datasets with
        remove (bool, optional): Remove datasets and clean up. Defaults to True.
    """
    # datasets = Dataset.list()
    datasets = renku_api.renku_dataset_list()
    if include is not None:
        datasets = [dataset for dataset in datasets if dataset.name in include]
    data_filter = [
        dataset.name
        for dataset in datasets
        if not any(data_key in keywords for data_key in dataset.keywords)
    ]
    if remove:
        [renku_dataset_remove(data_filt) for data_filt in data_filter]


def update_datasets_by_keyword(
    keyword: str,
    o_url: str,
    filter_ex: bool = True,
    filter_names: Optional[List[str]] = None,
    query_url: str = "https://renkulab.io/knowledge-graph/datasets?query=",
    data_url: str = "https://renkulab.io/knowledge-graph/datasets/",
    gitlab_url: str = "https://renkulab.io/gitlab",
    check_o_url: bool = True,
    n_latest: int = 9,
    all: bool = True,
):
    """Import and/or update all datasets that match a certain keyword

    Args:
        keyword (str): Keyword to match datasets
        o_url (str):  Orchestrator url that links all valid projects
        filter_ex (bool, optional): If existing datasets should be filtered automatically. Defaults to True.
        filter_names (Optional[List[str]], optional): Names to be filtered from the dataset list. Defaults to None.
        query_url (_type_, optional): URL to the knowledgebase dataset query API.
        data_url (_type_, optional): URL to the knowledgebase dataset API.
        gitlab_url (_type_, optional): General Gitlab url. Defaults to "https://renkulab.io/gitlab".
        all (bool, optional): If all datasets with matching keyword should be imported.
    """
    imp_ids, up_names = get_data_url_by_keyword(
        keyword=keyword,
        o_url=o_url,
        filter_ex=filter_ex,
        filter_names=filter_names,
        query_url=query_url,
        data_url=data_url,
        gitlab_url=gitlab_url,
        check_o_url=check_o_url,
        n_latest=n_latest,
    )
    if all:
        for id in imp_ids:
            renku_dataset_import(uri=id)
    else:
        if len(imp_ids) > 0:
            renku_dataset_import(uri=imp_ids[0])
    for nam in up_names:
        print(f"Updated dataset {nam}.")
        renku_dataset_update(names=[nam])
        renku_save()
    find_datasets_with_non_matching_keywords(
        keywords=[keyword], include=up_names, remove=True
    )


def update_dataset_files(urls: List[str], dataset_name: str):
    """Add or update a list of files to/in a specified dataset.

    Args:
        urls (List[str]): File paths to add/update
        dataset_name (str): Dataset name to add files to/update files in
    """
    # datasets = Dataset.list()
    datasets = renku_api.renku_dataset_list()
    name_list = [dataset.name for dataset in datasets]
    if dataset_name not in name_list:
        print(
            f"WARNING: Dataset {dataset_name} does not exist.\n"
            f"Files will not be added to any dataset."
        )
        return
    dataset = [data for data in datasets if data.name == dataset_name][0]
    valid_urls = [url for url in into_list(urls) if os.path.isfile(url)]
    dataset_files = [fi.path for fi in dataset.files]
    add_urls = [url for url in valid_urls if url not in dataset_files]
    if len(add_urls) > 0:
        renku_add_to_dataset(urls=add_urls, dataset_name=dataset_name)
        print(f"Added the following files to {dataset_name}:\n {add_urls}")
    return


def unlink_dataset_files(out_files: List[str], dataset_name: str, remove: bool = True):
    """Unlink files from a given dataset

    Args:
        out_files (List[str]): List of files to unlink
        dataset_name (str): Dataset name tounlink files from

    Raises:
        InputError: Dataset needs to refer to an existing dataset in the current project.
    """
    # datasets = Dataset.list()
    datasets = renku_api.renku_dataset_list()
    name_list = [dataset.name for dataset in datasets]
    if dataset_name not in name_list:
        raise InputError("Dataset {dataset_name} does not exist in this project.")
    dataset = [data for data in datasets if data.name == dataset_name][0]
    out_urls = [url for url in out_files if os.path.isfile(url)]
    dataset_files = [fi.path for fi in dataset.files]
    # What is with include as pattern? Can we replace all if renku doesn't complain for non-existing files?
    [
        renku_unlink_from_dataset(name=dataset_name, include=[out_url])
        for out_url in out_urls
        if out_url in dataset_files
    ]
    if remove:
        for out_url in out_urls:
            if os.path.exists(out_url):
                os.remove(out_url)


def link_files_by_prefix(
    keyword: str, prefix: List[str], data_name: str, dry_run: bool = False
):
    """Link files to a specific renku dataset, by specifying a keyword and the file prefixes.

    Args:
        keyword (str): Dataset keyword to select files from.
        prefix (List[str]): Prefix to select files by.
        data_name (str): Name of the dataset to link files to.
        dry_run (bool, optional): Check which files would be added without linking them. Defaults to False.
    """
    link_list: List = []
    prefix = [prefix] if not isinstance(prefix, List) else prefix  # type:ignore
    datasets = renku_api.renku_dataset_list()
    key_data = [
        dataset
        for dataset in datasets
        if any(key in keyword for key in dataset.keywords)
    ]
    for data in key_data:
        pat_list = [re.compile(pattern) for pattern in prefix]
        pat_files = [
            fi.path
            for fi in data.files
            if any(pattern.search(os.path.basename(fi.path)) for pattern in pat_list)
        ]
        link_list = link_list + pat_files
    if dry_run:
        nl = "\n"
        print(
            f"Run link_files_by_prefix with dry_run = False to link the following files to {data_name}:\n"
            f"{nl}{nl.join(link_list)}"
        )
    else:
        update_dataset_files(urls=link_list, dataset_name=data_name)
