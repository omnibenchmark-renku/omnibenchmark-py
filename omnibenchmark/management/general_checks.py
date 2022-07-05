"""General checks to ensure the enviroment and setup are as expected"""

from renku.ui.api.models.project import Project
from omnibenchmark.utils.exceptions import InputError
from typing import Union, Optional
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
    repo = project.client.repository
    os.chdir(current_dir)
    return True if repo.contains(".renku/metadata") else False


def find_orchestrator(
    benchmark_name: str,
    bench_url: str = "https://omnibenchmark.pages.uzh.ch/omni_dash/benchmarks",
    key_header: str = "Benchmark_name",
    o_header: str = "Orchestrator",
) -> Optional[str]:
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
    except Exception as e:
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
