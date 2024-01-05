from omnibenchmark.renku_commands import datasets as ren_datasets
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
    return_value = ren_datasets.renku_dataset_create(
        slug="mock_dataset", data_query_url="some.url"
    )
    assert isinstance(return_value, type(None))


def test_renku_dataset_create_for_dataset_slug_exist(
    mock_dataset_query, monkeypatch, get_renkuDataset_List
):
    def get_mock_status():
        return True

    monkeypatch.setattr(
        omnibenchmark.management.general_checks,
        "is_renku_project",
        lambda *args, **kwargs: get_mock_status(),
    )

    return_value = ren_datasets.renku_dataset_create(
        slug="mock_dataset", data_query_url="some.url"
    )
    assert isinstance(return_value, type(None))


@pytest.mark.renku_call
def test_renku_dataset_create_works():

    data_slug = "test_omnibench"
    data_object = ren_datasets.renku_dataset_create(
        slug=data_slug
    )
    remove_dataset_command().build().execute("test_omnibench")

    assert data_object.slug == data_slug


def test_renku_dataset_create_no_project_context(no_project_context):

    with pytest.raises(ProjectError, match=r"Directory is not a renku project*?"):
        ren_datasets.renku_dataset_create(slug="mock_dataset", data_query_url="some.url")


### Test renku_dataset_import
def test_renku_dataset_import_no_project_context(no_project_context):

    with pytest.raises(ProjectError, match=r"Directory is not a renku project*?"):
        ren_datasets.renku_dataset_import(uri="some.url")


@pytest.mark.renku_call
def test_renku_dataset_import_works():

    data_object = ren_datasets.renku_dataset_import(
        uri="https://renkulab.io/datasets/94638c493af44b5e8bc09b2351f6a8c2",
        slug="test_dataset",
    )
    assert os.path.exists("data/test_dataset/data_info_cellbench.json")
    shutil.rmtree("data/test_dataset", ignore_errors=True)
    remove_dataset_command().build().execute("test_dataset")


### Test renku_dataset_update
def test_renku_dataset_update_no_project_context(no_project_context):

    with pytest.raises(ProjectError, match=r"Directory is not a renku project*?"):
        ren_datasets.renku_dataset_update(slugs=["some_dataset", "another_datatset"])


def test_renku_dataset_update_no_input(monkeypatch):
    def get_mock_status():
        return True

    monkeypatch.setattr(
        omnibenchmark.management.general_checks,
        "is_renku_project",
        lambda *args, **kwargs: get_mock_status(),
    )
    with pytest.raises(errors.ParameterError, match=r"Either names, update_all*?"):
        ren_datasets.renku_dataset_update(slugs=[])


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
        ren_datasets.renku_dataset_update(slugs=["test2", "something"], update_all=True)


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
        ren_datasets.renku_dataset_update(
            slugs=[], include=["test2", "something"], update_all=True
        )


@pytest.mark.renku_call
def test_renku_dataset_update_works():

    res = ren_datasets.renku_dataset_update(slugs=[], update_all=True)
    assert res is None


### Test renku_add_to_dataset
def test_renku_add_to_dataset_no_project_context(no_project_context):

    with pytest.raises(ProjectError, match=r"Directory is not a renku project*?"):
        ren_datasets.renku_add_to_dataset(
            urls=["some_dataset", "another_datatset"], dataset_slug="some_dataset"
        )
