from omnibenchmark.management import general_checks
from omnibenchmark.utils.exceptions import InputError
from renku.core.errors import RequestError
import pytest
import requests

### Test is_renku_project
def test_is_renku_project_for_current_dir():
    assert not general_checks.is_renku_project()


def test_is_renku_project_for_non_exist_dir():
    with pytest.raises(Exception) as e_info:
        general_checks.is_renku_project("/non_existing/path")


### Test find_orchestrator
def test_find_orchestrator_matching_key(monkeypatch, mock_response_essential):

    def mock_get(*args, **kwargs):
        return mock_response_essential

    monkeypatch.setattr(requests, "get", mock_get)
    assert (
        general_checks.find_orchestrator("explicit")
        == "https://mocklab.io/kg/projects/another-orchestrator-path"
    )

### Test find_orchestrator multiple benchmark keys
def test_find_orchestrator_multi_matching_key(monkeypatch, mock_response_essential):

    def mock_get(*args, **kwargs):
        return mock_response_essential

    monkeypatch.setattr(requests, "get", mock_get)
    assert (
        general_checks.find_orchestrator("one")
        == "https://mocklab.io/kg/projects/orchestrator-path"
    )


def test_find_orchestrator_not_existing_url(monkeypatch, mock_response_essential):

    def mock_get(*args, **kwargs):
        mock_resp = mock_response_essential
        mock_resp.status_code = 404
        return mock_resp

    monkeypatch.setattr(requests, "get", mock_get)

    with pytest.raises(RequestError, match=r"Requested url not available:*?"):
        general_checks.find_orchestrator("omni_batch")


def test_find_orchestrator_not_existing_key(monkeypatch, mock_response_essential):
    
    def mock_get(*args, **kwargs):
        return mock_response_essential

    monkeypatch.setattr(requests, "get", mock_get)
    assert general_checks.find_orchestrator("omni") is None


@pytest.mark.api_call
def test_find_orchestrator_works():
    assert (
        general_checks.find_orchestrator("omni_batch_py")
        == "https://renkulab.io/knowledge-graph/projects/omnibenchmark/omni-batch-py/orchestrator-py"
    )
