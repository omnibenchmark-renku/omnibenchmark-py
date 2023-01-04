from omnibenchmark.utils import benchmark_queries as omni
import pytest

# Test get_orchestrator_projects_from_cicd_yaml
@pytest.mark.api_call
def test_get_orchestrator_projects_from_cicd_yaml_existing_benchmark():
    o_url = "https://renkulab.io/knowledge-graph/projects/omnibenchmark/omni-batch-py/orchestrator-py"
    assert (
        "omnibenchmark/omni-batch-py/cellbench-py"
        in omni.get_orchestrator_projects_from_cicd_yaml(o_url)
    )


def test_get_orchestrator_projects_from_cicd_yaml_exclude_stage():
    o_url = "https://renkulab.io/knowledge-graph/projects/omnibenchmark/omni-batch-py/orchestrator-py"
    project_list = omni.get_orchestrator_projects_from_cicd_yaml(
        o_url, exclude_stages=["metric_run"]
    )
    assert "omnibenchmark/omni-batch-py/lisi-py" not in project_list
