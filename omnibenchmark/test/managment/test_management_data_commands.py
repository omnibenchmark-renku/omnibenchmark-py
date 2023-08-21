from omnibenchmark.management import data_commands
import requests
import re

import pytest

# query_datasets_by_string
@pytest.mark.api_call
def test_query_entities_by_string_works():
    query_res = data_commands.query_entities_by_string("test")
    assert isinstance(query_res, list)
    assert "name" in query_res[0].keys()


# query_datasets_by_property
def test_query_datasets_by_property_with_matching_key(mock_entity_json, monkeypatch):
    class MockResponse:
        @staticmethod
        def json():
            return mock_entity_json

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    res = data_commands.query_datasets_by_property("mock")
    assert res[0]["slug"] == "mock_dataset"


def test_query_datasets_by_property_not_matching_key(mock_entity_json, monkeypatch):
    class MockResponse:
        @staticmethod
        def json():
            return mock_entity_json

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    res = data_commands.query_datasets_by_property("something")
    assert res == []


def test_query_datasets_by_property_other_property(mock_entity_json, monkeypatch):
    class MockResponse:
        @staticmethod
        def json():
            return mock_entity_json

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    res = data_commands.query_datasets_by_property(
        string="mock", match_string="A mock dataset", property_name="name"
    )
    assert res[0]["slug"] == "mock_dataset"


# filter_existing
def test_filter_existing_with_existing(get_renkuDataset_List, mock_entity_json):
    imp_list, up_list = data_commands.filter_existing(mock_entity_json)
    assert imp_list == []
    assert up_list == mock_entity_json


def test_filter_existing_not_existing(get_renkuDataset_List, mock_entity_json):
    mock_entity_json[0]["slug"] = "something"
    imp_list, up_list = data_commands.filter_existing(mock_entity_json)
    assert imp_list == mock_entity_json
    assert up_list == []


### Assumptions do not hold after renku api change.
#@pytest.mark.api_call
#def test_get_data_info_by_url_works():
#    query_res = data_commands.query_entities_by_string("test")
#    query_url = query_res[0]["_links"][0]["href"]
#    data_info = data_commands.get_data_info_by_url(query_url)
#    assert data_info["name"] == query_res[0]["slug"]
#    assert "url" in data_info.keys()


# get_field_by_dataset_property
def test_get_ref_by_dataset_property_no_filter(mock_entity_json, monkeypatch):
    class MockResponse:
        @staticmethod
        def json():
            return mock_entity_json

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    res1, res2 = data_commands.get_ref_by_dataset_property("mock")
    assert res1 == ["https://this_is_a_mo.ck"]
    assert res2 == []


def test_get_ref_by_dataset_property_filter_names(mock_entity_json, monkeypatch):
    class MockResponse:
        @staticmethod
        def json():
            return mock_entity_json

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    res1, res2 = data_commands.get_ref_by_dataset_property(
        "mock", filter_names="mock_dataset"
    )
    assert res1 == []
    assert res2 == []


def test_get_ref_by_dataset_property_with_filter(
    mock_entity_json, monkeypatch, get_renkuDataset_List
):
    class MockResponse:
        @staticmethod
        def json():
            return mock_entity_json

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    res1, res2 = data_commands.get_ref_by_dataset_property("mock", filter_ex=True)
    assert res1 == []
    assert res2 == ["mock_dataset"]


def test_get_ref_by_dataset_property_with_filter_no_match(
    mock_entity_json, monkeypatch, get_renkuDataset_List
):
    mock_entity_json[0]["slug"] = "something"

    class MockResponse:
        @staticmethod
        def json():
            return mock_entity_json

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    res1, res2 = data_commands.get_ref_by_dataset_property("mock", filter_ex=True)
    assert res1 == ["https://this_is_a_mo.ck"]
    assert res2 == []


def test_get_ref_by_dataset_property_no_data(
    mock_entity_json, monkeypatch, get_renkuDataset_List
):
    class MockResponse:
        @staticmethod
        def json():
            return []

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    res1, res2 = data_commands.get_ref_by_dataset_property("mock", filter_ex=True)
    assert res1 == []
    assert res2 == []


# find_dataset_linked_to_wflow
@pytest.mark.api_call
def test_find_dataset_linked_to_wflow(mock_dataset_info):
    linked = data_commands.find_dataset_linked_to_wflow([mock_dataset_info])
    assert linked == []


# filter_duplicated_names
@pytest.mark.api_call
def test_filter_duplicated_names_works(
    mock_dataset_info, monkeypatch, mock_dataset_json
):
    mock_copy = mock_dataset_info.copy()
    mock_copy["identifier"] = "XXXXXX"
    info_list = [mock_dataset_info, mock_copy]

    class MockResponse:
        @staticmethod
        def json():
            return mock_dataset_json

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    uni_dat = data_commands.filter_duplicated_names(info_list)
    assert uni_dat == [mock_copy]


@pytest.mark.api_call
def test_filter_duplicated_names_identical_data(
    mock_dataset_info, monkeypatch
):
    mock_copy = mock_dataset_info.copy()
    mock_copy["name"] = "new"
    info_list = [mock_dataset_info, mock_copy]
    info_list = [mock_dataset_info, mock_dataset_info]


    uni_dat = data_commands.filter_duplicated_names(info_list)
    assert uni_dat == [mock_dataset_info]


@pytest.mark.api_call
def test_filter_duplicated_names_no_dup(
    mock_dataset_info, monkeypatch
):
    info_list = [mock_dataset_info, mock_dataset_info]

    uni_dat = data_commands.filter_duplicated_names(info_list)
    assert uni_dat == [mock_dataset_info]


# get_origin_dataset_ids
def test_get_origin_dataset_infos_unique_ref(monkeypatch, mock_dataset_info):
    class MockResponse:
        @staticmethod
        def json():
            return mock_dataset_info

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    data_ids = data_commands.get_origin_dataset_infos(["idx"])
    assert data_ids == [mock_dataset_info]


def test_get_origin_dataset_infos_with_sameas(monkeypatch, mock_dataset_info):

    mock_dataset_info["sameAs"] = "idy"

    class MockResponse:
        @staticmethod
        def json():
            return mock_dataset_info

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    data_ids = data_commands.get_origin_dataset_infos(["idx"])
    assert data_ids == [mock_dataset_info]


def test_get_origin_dataset_infos_with_noname(monkeypatch, mock_dataset_info):

    del mock_dataset_info["slug"]

    class MockResponse:
        @staticmethod
        def json():
            return mock_dataset_info

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    data_ids = data_commands.get_origin_dataset_infos(["idx"])
    assert data_ids == []


### Assumptions do not hold after renku api change.
#@pytest.mark.api_call
#def test_get_origin_dataset_infos_works():
#    query_res = data_commands.query_entities_by_string("test")
#    query_url = query_res[0]["_links"][0]["href"]
#
#    data_ids = data_commands.get_origin_dataset_infos([query_url])
#    assert data_ids[0]["name"] == query_res[0]["slug"]


# Check_orchestrator
@pytest.mark.api_call
def test_check_orchestrator_existing(monkeypatch, mock_dataset_info):
    o_url = "https://renkulab.io/knowledge-graph/projects/omnibenchmark/orchestrator"
    project_info = {"identifier": 12385}
    project_mod = {"identifier": 12779}

    class MockResponse:
        @staticmethod
        def json():
            return project_info

    class MockMod:
        @staticmethod
        def json():
            return project_mod

    def get_project_info(*args, **kwargs):
        if mock_dataset_info["project"]["_links"][0]["href"] in args:
            return MockMod()
        else:
            return MockResponse()

    monkeypatch.setattr(requests, "get", get_project_info)
    o_check = data_commands.check_orchestrator(mock_dataset_info, o_url="some/url")
    assert o_check == mock_dataset_info["url"]


# get_data_url_by_keyword
def test_get_data_url_by_keyword_no_datasets(mock_dataset_json, monkeypatch):
    class MockResponse:
        @staticmethod
        def json():
            return []

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    assert data_commands.get_data_url_by_keyword("mock", "some/path") == ([], [])


# link_files_by_prefix
def test_link_files_by_prefix_existing_file(get_renkuDataset_List, capsys):
    data_commands.link_files_by_prefix(
        keyword="mock", prefix=["genes"], data_name="some", dry_run=True
    )
    captured = capsys.readouterr()
    assert re.match(
        r"Run link_files_by_prefix with dry_run = False to link the following files to some:\n\nsome/path/to/genes_file.txt*",
        captured.out,
    )


def test_link_files_by_prefix_non_keyword(get_renkuDataset_List, capsys):
    data_commands.link_files_by_prefix(
        keyword="quatsch", prefix=["genes"], data_name="some", dry_run=True
    )
    captured = capsys.readouterr()
    assert re.match(
        r"Run link_files_by_prefix with dry_run = False to link the following files to some:\n\n\n",
        captured.out,
    )


def test_link_files_by_prefix_prefix_string(get_renkuDataset_List, capsys):
    data_commands.link_files_by_prefix(
        keyword="mock", prefix="genes", data_name="some", dry_run=True
    )
    captured = capsys.readouterr()
    assert re.match(
        r"Run link_files_by_prefix with dry_run = False to link the following files to some:\n\nsome/path/to/genes_file.txt*",
        captured.out,
    )
