from omnibenchmark.renku_commands import datasets
import omnibenchmark.management.general_checks
from renku.command.dataset import remove_dataset_command, file_unlink_command
from renku.core import errors
from renku.ui.api import Dataset
from omnibenchmark.utils.exceptions import ProjectError
import pytest
import os
import shutil

### Test renku_dataset_create
def test_renku_dataset_create_for_existing_dataset(get_renkuDataset_List, monkeypatch):
    def get_mock_status():
        return True

    monkeypatch.setattr(
        omnibenchmark.management.general_checks,
        "is_renku_project",
        lambda *args, **kwargs: get_mock_status(),
    )
    return_value = datasets.renku_dataset_create(name="mock_dataset", kg_url="some.url")
    assert isinstance(return_value, type(None))


def test_renku_dataset_create_for_dataset_name_exist(mock_dataset_query, monkeypatch):
    def get_mock_status():
        return True

    monkeypatch.setattr(
        omnibenchmark.management.general_checks,
        "is_renku_project",
        lambda *args, **kwargs: get_mock_status(),
    )

    return_value = datasets.renku_dataset_create(name="mock_dataset", kg_url="some.url")
    assert isinstance(return_value, type(None))


@pytest.mark.renku_call
def test_renku_dataset_create_works():

    data_name = "test_omnibench"
    data_object = datasets.renku_dataset_create(
        name=data_name, kg_url="https://renkulab.io/knowledge-graph"
    )
    remove_dataset_command().build().execute("test_omnibench")

    assert data_object.name == data_name


def test_renku_dataset_create_no_project_context(no_project_context):

    with pytest.raises(ProjectError, match=r"Directory is not a renku project*?"):
        datasets.renku_dataset_create(name="mock_dataset", kg_url="some.url")


### Test renku_dataset_import
def test_renku_dataset_import_no_project_context(no_project_context):

    with pytest.raises(ProjectError, match=r"Directory is not a renku project*?"):
        datasets.renku_dataset_import(uri="some.url")


@pytest.mark.renku_call
def test_renku_dataset_import_works():

    data_object = datasets.renku_dataset_import(
        uri="https://renkulab.io/datasets/94638c493af44b5e8bc09b2351f6a8c2",
        name="test_dataset",
    )
    assert os.path.exists("data/test_dataset/data_info_cellbench.json")
    shutil.rmtree("data/test_dataset", ignore_errors=True)
    remove_dataset_command().build().execute("test_dataset")


### Test renku_dataset_update
def test_renku_dataset_update_no_project_context(no_project_context):

    with pytest.raises(ProjectError, match=r"Directory is not a renku project*?"):
        datasets.renku_dataset_update(names=["some_dataset", "another_datatset"])


def test_renku_dataset_update_no_input(monkeypatch):
    def get_mock_status():
        return True

    monkeypatch.setattr(
        omnibenchmark.management.general_checks,
        "is_renku_project",
        lambda *args, **kwargs: get_mock_status(),
    )
    with pytest.raises(errors.ParameterError, match=r"Either names, update_all*?"):
        datasets.renku_dataset_update(names=[])


def test_renku_dataset_update_ambigous_inputs(monkeypatch):
    def get_mock_status():
        return True

    monkeypatch.setattr(
        omnibenchmark.management.general_checks,
        "is_renku_project",
        lambda *args, **kwargs: get_mock_status(),
    )

    with pytest.raises(
        errors.ParameterError, match=r"Cannot pass dataset names with update_all"
    ):
        datasets.renku_dataset_update(names=["test2", "something"], update_all=True)


def test_renku_dataset_update_ambigous_inputs2(monkeypatch):
    def get_mock_status():
        return True

    monkeypatch.setattr(
        omnibenchmark.management.general_checks,
        "is_renku_project",
        lambda *args, **kwargs: get_mock_status(),
    )

    with pytest.raises(
        errors.ParameterError, match=r"Cannot pass include/exclude with update_all"
    ):
        datasets.renku_dataset_update(
            names=[], include=["test2", "something"], update_all=True
        )


@pytest.mark.renku_call
def test_renku_dataset_update_works():

    res = datasets.renku_dataset_update(names=[], update_all=True)
    assert res is None


### Test renku_add_to_dataset
def test_renku_add_to_dataset_no_project_context(no_project_context):

    with pytest.raises(ProjectError, match=r"Directory is not a renku project*?"):
        datasets.renku_add_to_dataset(
            urls=["some_dataset", "another_datatset"], dataset_name="some_dataset"
        )


@pytest.mark.renku_call
def test_renku_add_to_dataset_works():
    test_file = "data/utils_test/test_file.txt"
    text_file = open(test_file, "w")
    text_file.write("This is a test for renku dataset add")
    text_file.close()

    res = datasets.renku_add_to_dataset(urls=[test_file], dataset_name="utils_test")
    datasets = Dataset.list()
    data_files = [dataset.files for dataset in datasets if dataset.name == "utils_test"]
    assert test_file in data_files
    file_unlink_command().build().execute(name="utils_test", include=test_file)
