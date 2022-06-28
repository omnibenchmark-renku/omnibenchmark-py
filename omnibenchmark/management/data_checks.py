"""Checks concerning (usually renku) datasets"""

from renku.ui.api.models.dataset import Dataset
import requests
from typing import Union
import os


def renku_dataset_exist(name: str, path: Union[os.PathLike, str] = os.getcwd()) -> bool:
    """Check if a renku dataset with a specific name already exist at a certain project path.

    Args:
        name (str): Dataset name
        path (PathLike, optional): Project path to check. Defaults to ".".

    Returns:
        bool: True/False a dataset with that name exist in the project at that path.
    """

    current_dir = os.getcwd()
    os.chdir(path)
    datasets = Dataset.list()
    matches = [dataset.name for dataset in datasets if dataset.name == name]
    os.chdir(current_dir)
    return True if len(matches) >= 1 else False


def dataset_name_exist(name: str, kg_url: str) -> bool:
    """Check if a renku dataset with a defined name already exists in the knowledge base.

    Args:
        name (str): Name to query
        kg_url (str): Url of the knowledge base to query

    Returns:
        bool: True/False, if a dataset with that name already exist
    """

    url = kg_url + "/datasets?query=" + name
    response = requests.get(url)
    return True if name in [item["name"] for item in response.json()] else False
