import omnibenchmark.utils.auto_input as omni
from omnibenchmark.utils.exceptions import ParameterError
import renku.ui.api.models.dataset
import pytest
import re

### Test auto input functions

# join_parameter
def test_get_input_files_from_prefix_works(mock_api_Dataset, mock_prefix, monkeypatch):
    del mock_prefix["count_file"]

    def get_mock_list():
        return [mock_api_Dataset]

    monkeypatch.setattr(
        renku.ui.api.models.dataset.Dataset,
        "list",
        lambda *args, **kwargs: get_mock_list(),
    )

    test_join = omni.get_input_files_from_prefix(
        input_prefix=mock_prefix, keyword=["mock", "some"]
    )
    assert test_join == {
        "mock_dataset": {"dim_red_file": "some/path/to/genes_file.txt"}
    }


def test_get_input_files_from_prefix_works_incomplete(
    mock_api_Dataset, mock_prefix, monkeypatch, capsys
):
    def get_mock_list():
        return [mock_api_Dataset]

    monkeypatch.setattr(
        renku.ui.api.models.dataset.Dataset,
        "list",
        lambda *args, **kwargs: get_mock_list(),
    )

    test_join = omni.get_input_files_from_prefix(
        input_prefix=mock_prefix, keyword=["mock", "some"]
    )
    captured = capsys.readouterr()
    assert test_join == {}
    assert re.match(
        r"WARNING:Could not find any input file matching the following pattern*?",
        captured.out,
    )


def test_get_input_files_from_prefix_works_regexpr(
    mock_api_Dataset, mock_prefix, monkeypatch
):
    del mock_prefix["count_file"]
    mock_prefix["dim_red_file"] = ["features", "file"]

    def get_mock_list():
        return [mock_api_Dataset]

    monkeypatch.setattr(
        renku.ui.api.models.dataset.Dataset,
        "list",
        lambda *args, **kwargs: get_mock_list(),
    )

    test_join = omni.get_input_files_from_prefix(
        input_prefix=mock_prefix, keyword=["mock", "some"]
    )
    assert test_join == {
        "mock_dataset": {"dim_red_file": "some/path/to/genes_file.txt"}
    }


# get_parameter_from_dataset
def test_get_parameter_from_dataset_works(mock_paramapi_Dataset, monkeypatch):
    mock_paramapi_Dataset._files = [mock_paramapi_Dataset._files[0]]

    def get_mock_list():
        return [mock_paramapi_Dataset]

    monkeypatch.setattr(
        renku.ui.api.models.dataset.Dataset,
        "list",
        lambda *args, **kwargs: get_mock_list(),
    )

    test_join = omni.get_parameter_from_dataset(
        names=["param2"], keyword=["mock_param", "some"]
    )
    assert test_join == {"param2": ["test", "hvg", "dim"]}


def test_get_parameter_from_dataset_to_man_files(mock_paramapi_Dataset, monkeypatch):
    def get_mock_list():
        return [mock_paramapi_Dataset]

    monkeypatch.setattr(
        renku.ui.api.models.dataset.Dataset,
        "list",
        lambda *args, **kwargs: get_mock_list(),
    )
    with pytest.raises(
        ParameterError, match=r"Could not identify parameter json file.*?"
    ):
        omni.get_parameter_from_dataset(
            names=["param2"], keyword=["mock_param", "some"]
        )


def test_get_parameter_from_dataset_not_ex_parameter(
    mock_paramapi_Dataset, monkeypatch, capsys
):
    mock_paramapi_Dataset._files = [mock_paramapi_Dataset._files[0]]

    def get_mock_list():
        return [mock_paramapi_Dataset]

    monkeypatch.setattr(
        renku.ui.api.models.dataset.Dataset,
        "list",
        lambda *args, **kwargs: get_mock_list(),
    )

    test_join = omni.get_parameter_from_dataset(
        names=["param2", "param3"], keyword=["mock_param"]
    )
    captured = capsys.readouterr()
    assert test_join == {"param2": ["test", "hvg", "dim"]}
    assert re.match(
        r"WARNING: Could not find a matching parameter for param3*?", captured.out
    )


def test_get_parameter_from_dataset_not_matching_keyword(
    mock_paramapi_Dataset, monkeypatch
):
    def get_mock_list():
        return [mock_paramapi_Dataset]

    monkeypatch.setattr(
        renku.ui.api.models.dataset.Dataset,
        "list",
        lambda *args, **kwargs: get_mock_list(),
    )

    test_join = omni.get_parameter_from_dataset(
        names=["param2", "param3"], keyword=["quatsch"]
    )
    assert test_join == {}


def test_get_parameter_from_dataset_not_matching_names(
    mock_paramapi_Dataset, monkeypatch
):
    mock_paramapi_Dataset._files = [mock_paramapi_Dataset._files[0]]

    def get_mock_list():
        return [mock_paramapi_Dataset]

    monkeypatch.setattr(
        renku.ui.api.models.dataset.Dataset,
        "list",
        lambda *args, **kwargs: get_mock_list(),
    )

    test_join = omni.get_parameter_from_dataset(
        names=["param4", "param3"], keyword=["mock_param"]
    )
    assert test_join == {}
