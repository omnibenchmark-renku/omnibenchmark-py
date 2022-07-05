from omnibenchmark.management import general_checks
from omnibenchmark.utils.exceptions import InputError
import pytest
import requests

### Test is_renku_project
def test_is_renku_project_for_current_dir():
    assert not general_checks.is_renku_project()


def test_is_renku_project_for_non_exist_dir():
    with pytest.raises(Exception) as e_info:
        general_checks.is_renku_project("/non_existing/path")


### Test find_orchestrator
def test_find_orchestrator_matching_key(monkeypatch, mock_html_content):
    class MockResponse:
        def __init__(self):
            self.content = mock_html_content

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)
    assert (
        general_checks.find_orchestrator("omni_batch")
        == "https://renkulab.io/knowledge-graph/projects/omnibenchmark/orchestrator"
    )


def test_find_orchestrator_not_existing_header(monkeypatch, mock_html_content):
    class MockResponse:
        def __init__(self):
            self.content = mock_html_content

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    with pytest.raises(InputError, match=r"Could not find columns with names new*?"):
        general_checks.find_orchestrator("omni_batch", key_header="new")


def test_find_orchestrator_not_existing_key(monkeypatch, mock_html_content):
    class MockResponse:
        def __init__(self):
            self.content = mock_html_content

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)
    assert general_checks.find_orchestrator("omni") is None


@pytest.mark.api_call
def test_find_orchestrator_works():
    assert (
        general_checks.find_orchestrator("omni_batch_py")
        == "https://renkulab.io/knowledge-graph/projects/omnibenchmark/omni-batch-py/orchestrator-py"
    )
