"""Commands related to import and update relevant datasets"""
from typing import List, Mapping, Any, Optional, Tuple
from renku.ui.api.models.dataset import Dataset
from omnibenchmark.renku_commands.datasets import (
    renku_dataset_import,
    renku_dataset_update,
    renku_add_to_dataset,
)
import requests
import os.path
import gitlab
from iteration_utilities import unique_everseen  # type: ignore

# Find datasets by string
def query_datasets_by_string(
    string: str, url: str = "https://renkulab.io/knowledge-graph/datasets?query="
) -> List[Mapping[Any, Any]]:
    query_url = url + string
    response = requests.get(query_url)
    return response.json()


# Find dataset by match of property
def query_datasets_by_property(
    string: str,
    url: str = "https://renkulab.io/knowledge-graph/datasets?query=",
    match_string: Optional[str] = None,
    property_name: str = "keywords",
) -> List[Mapping[Any, Any]]:
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
    update_list: List = []
    import_list: List = []
    datasets = Dataset.list()
    name_list = [dataset.name for dataset in datasets]
    for data in data_json:
        if data["name"] in name_list:
            update_list.append(data)
        else:
            import_list.append(data)
    return import_list, update_list


# Get dataset field by matching property
def get_field_by_dataset_property(
    string: str,
    url: str = "https://renkulab.io/knowledge-graph/datasets?query=",
    property_name: str = "keywords",
    field: str = "identifier",
    filter_ex: bool = False,
) -> Tuple[List[str], List[str]]:
    data_json = query_datasets_by_property(
        string=string, url=url, property_name=property_name
    )
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
    query_url = url + id
    response = requests.get(query_url)
    return response.json()


def find_dataset_linked_to_wflow(
    info_list: List[Mapping], top: int = 2, filter_pat: str = "meta"
) -> List[Mapping]:
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
                + data_file
                + "/lineage"
            )
            if "message" not in file_lineage.json().keys():
                origin_info.append(info)
                return origin_info
    return origin_info


def filter_duplicated_names(info_list: List[Mapping]) -> List[Mapping]:
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
            all_datasets = requests.get(
                list(dup_project)[0] + "/datasets"
            )  # type:ignore
            all_ids = [dat["identifier"] for dat in all_datasets.json()]
            origin_info = [info for info in dup_info if info["identifier"] in all_ids]
        else:
            origin_info = find_dataset_linked_to_wflow(dup_info)
        if len(origin_info) == 0:
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
    all_infos: List = []
    for data_id in ids:
        data_info = get_data_info_by_id(id=data_id, url=url)
        if "sameAs" in data_info.keys():
            if not data_info["sameAs"] == data_info["url"]:
                same_id = data_info["sameAs"].split("/")[
                    -1
                ]  ## Unstable string manipulation??
                data_info = get_data_info_by_id(id=same_id, url=url)
        if data_info not in all_infos and "name" in data_info.keys():
            all_infos.append(data_info)
    origin_infos = filter_duplicated_names(all_infos)
    return origin_infos


def get_project_info_from_url(project_url=str) -> Mapping[Any, Any]:
    response = requests.get(project_url)
    return response.json()


def check_orchestrator(
    data_info: Mapping, o_url: str, gitlab_url: str = "https://renkulab.io/gitlab"
) -> Optional[str]:
    project_url = data_info["project"]["_links"][0]["href"]
    project_info = get_project_info_from_url(project_url)
    o_info = get_project_info_from_url(o_url)
    renku_git = gitlab.Gitlab(gitlab_url)
    o_git = renku_git.projects.get(o_info["identifier"])
    success = o_git.pipelines.list(status="success")
    bridge_projects: List = []
    for pipe in success:
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
    query_url: str = "https://renkulab.io/knowledge-graph/datasets?query=",
    data_url: str = "https://renkulab.io/knowledge-graph/datasets/",
    gitlab_url: str = "https://renkulab.io/gitlab",
) -> Tuple[List[str], List[str]]:
    all_ids, up_exist = get_field_by_dataset_property(
        string=keyword, url=query_url, filter_ex=filter_ex
    )
    if len(all_ids) + len(up_exist) < 1:
        print(f"WARNING:No datasets found with keyword {keyword}")
        return [], []
    origin_infos = get_origin_dataset_ids(ids=all_ids, url=data_url)
    if len(origin_infos) + len(up_exist) < 1:
        print(
            f"WARNING:Could not identify dataset sources. Please check each of {data_url}{all_ids} to make sure they are the intended source"
        )
        return [], []
    omni_ids = [
        check_orchestrator(data_info=info, o_url=o_url, gitlab_url=gitlab_url)
        for info in origin_infos
    ]
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


def update_datasets_by_keyword(
    keyword: str,
    o_url: str,
    filter_ex: bool = True,
    query_url: str = "https://renkulab.io/knowledge-graph/datasets?query=",
    data_url: str = "https://renkulab.io/knowledge-graph/datasets/",
    gitlab_url: str = "https://renkulab.io/gitlab",
):
    imp_ids, up_names = get_data_url_by_keyword(
        keyword=keyword,
        o_url=o_url,
        filter_ex=filter_ex,
        query_url=query_url,
        data_url=data_url,
        gitlab_url=gitlab_url,
    )
    for id in imp_ids:
        renku_dataset_import(uri=id)
    for nam in up_names:
        print(f"Updated dataset {nam}.")
        renku_dataset_update(names=[nam])


def update_dataset_files(urls: List[str], dataset_name: str):
    datasets = Dataset.list()
    name_list = [dataset.name for dataset in datasets]
    if dataset_name not in name_list:
        print(
            f"WARNING: Dataset {dataset_name} does not exist.\n"
            f"Files will not be added to any dataset."
        )
        return
    dataset = [data for data in datasets if data.name == dataset_name][0]
    valid_urls = [url for url in urls if os.path.isfile(url)]
    dataset_files = [fi.path for fi in dataset.files]
    add_urls = [url for url in valid_urls if url not in dataset_files]
    if len(add_urls) > 0:
        renku_add_to_dataset(urls=add_urls, dataset_name=dataset_name)
        print(f"Added the following files to {dataset_name}:\n {add_urls}")
    return
