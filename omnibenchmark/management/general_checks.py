"""General checks to ensure the enviroment and setup are as expected"""

from renku.ui.api.models.project import Project
from omnibenchmark.utils.exceptions import InputError
from renku.core.errors import RequestError
from omnibenchmark.utils.general import into_list
from omnibenchmark.utils.local_cache.config import local_bench_cat_data
from omnibenchmark.utils.local_cache.sync import bench_cat_url
from typing import Union, Optional, List, Mapping
import warnings
import os
import requests
import json


def is_renku_project(path: Union[os.PathLike, str] = os.getcwd()) -> bool:
    """Checks if a project is an initialized renku project.
    Args:
        path (Pathlike, str, optional): A path to check. Defaults to ".".

    Returns:
        bool: True if project is a renku project.
    """
    current_dir = os.getcwd()
    os.chdir(path)
    project = Project()
    repo = project.repository
    os.chdir(current_dir)
    return True if '.renku/metadata.yml' in repo.files else False


def get_bench_essentials(
    bench_url: str = bench_cat_url,
    local_cache: bool = False
) -> Union[Mapping, List]:
    if local_cache:
        if os.path.exists(local_bench_cat_data):
            with open(local_bench_cat_data, 'r') as f:
                data = json.load(f)
        else:
            warnings.warn(f'Warning: Could not detect local cache. \n Checking {bench_url} instead.')
            data = None
    if not local_cache or data is None:
        r = requests.get(bench_url)
        if r.status_code == 404:
            raise RequestError( f'Requested url not available: {bench_url}')
        data = r.json()
    return data


def find_orchestrator(
    benchmark_name: str,
    bench_url: str = bench_cat_url,
    local_cache: bool = False
) -> Optional[str]:
    """Get the orchestrator url from the benchmark name.

    Args:
        benchmark_name (str): Name of the benchmark 
        bench_url (str, optional): Url to the "essentials" orchestrator file with all benchmark-specific infos. Defaults to bench_cat_url.
        local_cache (bool, optional): If the essentials  orchestrator file should be loaded from cache. Defaults to False.

    Returns:
        Optional[str]: orchestrator url
    """
    data = get_bench_essentials(bench_url=bench_url, local_cache=local_cache)
    o_url = [bench["orchestrator_url"] for bench in data if benchmark_name in into_list(bench["benchmark_names"])]
    if len(o_url) != 1:
        warnings.warn(
            f"WARNING: Could not find benchmark associated to {benchmark_name}.\n"
            f"Check {bench_url} for existing benchmarks.\n"
            f"Integration with existing projects is not possible."
        )
        return None
    return o_url[0]


def get_benchmark_groups(
    field_name: str,
    bench_url: str = bench_cat_url,
    local_cache: bool = False
) -> List[str]:
    """Get an overview of all available benchmarks 

    Args:
        field_name (str): Field to retrieve, must be part of the essentials orchestrator yaml file, e.g., 'orchestrator_url'
        bench_url (str, optional): Url to the essentials orchestrator file. Defaults to bench_cat_url.
        local_cache (bool, optional): If the essentials orchestrator file should be loaded from cache. Defaults to False.

    Raises:
        InputError: raised if field name is not present in the essentials orchestrator file

    Returns:
        List[str]: A list of the specified field from all available benchmarks. 
    """
    
    data = get_bench_essentials(bench_url=bench_url, local_cache=local_cache)
    entries = [dat[field_name] for dat in data if field_name in dat.keys()]
    concat_entries = [entri if not isinstance(entri, list) else ', '.join(entri) for entri in entries]

    if len(entries) < 1:
        raise InputError(
            f"Could not find fields with names {field_name}.\n"
            f"Please check {bench_url} for the correct fields."
        )

    return concat_entries