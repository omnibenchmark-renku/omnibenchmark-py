"""General checks to ensure the enviroment and setup are as expected"""

from renku.ui.api.models.project import Project
from omnibenchmark.utils.exceptions import InputError
from typing import Union, Optional, List
import os
import lxml.html as lh
import requests


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
    return True if repo.contains(".renku/metadata") else False


def find_orchestrator(
    benchmark_name: str,
    bench_url: str = "https://omnibenchmark.pages.uzh.ch/omb-site/p/benchmarks",
    key_header: str = "Benchmark_name",
    o_header: str = "Orchestrator",
) -> Optional[str]:
    """Assigns an orchestrator url based on the benchmark name by checking the omnibenchmark website.

    Args:
        benchmark_name (str): Name of the benchmark that thge object is part of.
        bench_url (_type_, optional): url to the omnibenchmark site with benchmark associations.
        key_header (str, optional): Header/column name specifying the benchmark names. Defaults to "Benchmark_name".
        o_header (str, optional): Header/column name specifying the orchestrator names. Defaults to "Orchestrator".

    Raises:
        InputError: Key_header and o_header need to be valid column names

    Returns:
        Optional[str]: Url to the orchestrator taht is linked to a specified benchmark.
    """
    bench_html = requests.get(bench_url)
    doc = lh.fromstring(bench_html.content)
    tr_elements = doc.xpath("//tr")
    header = tr_elements[0]
    col_num = 0
    for field in header:
        if field.text_content() == key_header:
            nam_col = col_num
        if field.text_content() == o_header:
            o_col = col_num
        col_num += 1

    try:
        nam_col, o_col
    except Exception:
        raise InputError(
            f"Could not find columns with names {key_header} and/or {o_header}.\n"
            f"Please check {bench_url} for the correct column names."
        )

    o_obj = [
        tr_ele[o_col]
        for tr_ele in tr_elements
        if benchmark_name in tr_ele[nam_col].text_content().split(",")
    ]
    if len(o_obj) < 1:
        print(
            f"WARNING: Could not find benchmark associated to {benchmark_name}.\n"
            f"Check {bench_url} for existing benchmarks.\n"
            f"Integration with existing projects is not possible."
        )
        return None
    o_url = o_obj[0].text_content()
    return o_url


def get_benchmark_groups(
    field_name: str,
    bench_url: str = "https://omnibenchmark.pages.uzh.ch/omb-site/p/benchmarks",
) -> List[str]:
    """Get all available benchmark groups as listed on bench_url

    Args:
        field_name (str): Table header name, with the entries to display
        bench_url (_type_, optional): Defaults to "https://omnibenchmark.pages.uzh.ch/omb-site/p/benchmarks".

    Raises:
        InputError: Raised if field name can not be found at bench_url

    Returns:
        List[str]: List with all entries for field_name at bench_url
    """
    bench_html = requests.get(bench_url)
    doc = lh.fromstring(bench_html.content)
    tr_elements = doc.xpath("//tr")
    header = tr_elements[0]
    col_num = 0
    for field in header:
        if field.text_content() == field_name:
            field_col = col_num
        col_num += 1

    try:
        field_col
    except Exception:
        raise InputError(
            f"Could not find columns with names {field_name}.\n"
            f"Please check {bench_url} for the correct column names."
        )

    entries = [tr_ele[field_col].text_content() for tr_ele in tr_elements[1:]]
    return entries
