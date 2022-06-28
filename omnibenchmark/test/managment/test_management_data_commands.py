from omnibenchmark.management import data_commands
import requests

import pytest

# query_datasets_by_string
@pytest.mark.api_call
def test_query_datasets_by_string_works():
    query_res = data_commands.query_datasets_by_string("test")
    assert isinstance(query_res, list)
    assert "name" in query_res[0].keys()


# query_datasets_by_property
def test_query_datasets_by_property_with_matching_key(mock_dataset_json, monkeypatch):
    class MockResponse:
        @staticmethod
        def json():
            return mock_dataset_json

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    res = data_commands.query_datasets_by_property("mock")
    assert res[0]["name"] == "mock_dataset"


def test_query_datasets_by_property_not_matching_key(mock_dataset_json, monkeypatch):
    class MockResponse:
        @staticmethod
        def json():
            return mock_dataset_json

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    res = data_commands.query_datasets_by_property("something")
    assert res == []


def test_query_datasets_by_property_other_property(mock_dataset_json, monkeypatch):
    class MockResponse:
        @staticmethod
        def json():
            return mock_dataset_json

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    res = data_commands.query_datasets_by_property(
        string="mock", match_string="XXXXXX", property_name="identifier"
    )
    assert res[0]["name"] == "mock_dataset"


# filter_existing
def test_filter_existing_with_existing(get_renkuDataset_List, mock_dataset_json):
    imp_list, up_list = data_commands.filter_existing(mock_dataset_json)
    assert imp_list == []
    assert up_list == mock_dataset_json


def test_filter_existing_not_existing(get_renkuDataset_List, mock_dataset_json):
    mock_dataset_json[0]["name"] = "something"
    imp_list, up_list = data_commands.filter_existing(mock_dataset_json)
    assert imp_list == mock_dataset_json
    assert up_list == []


@pytest.mark.api_call
def test_get_data_info_by_id_works():
    query_res = data_commands.query_datasets_by_string("test")
    query_id = query_res[0]["identifier"]
    data_info = data_commands.get_data_info_by_id(query_id)
    assert data_info["name"] == query_res[0]["name"]
    assert "url" in data_info.keys()


# get_field_by_dataset_property
def test_get_field_by_dataset_property_no_filter(mock_dataset_json, monkeypatch):
    class MockResponse:
        @staticmethod
        def json():
            return mock_dataset_json

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    res1, res2 = data_commands.get_field_by_dataset_property("mock")
    assert res1 == ["XXXXXX"]
    assert res2 == []


def test_get_field_by_dataset_property_with_filter(
    mock_dataset_json, monkeypatch, get_renkuDataset_List
):
    class MockResponse:
        @staticmethod
        def json():
            return mock_dataset_json

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    res1, res2 = data_commands.get_field_by_dataset_property("mock", filter_ex=True)
    assert res1 == []
    assert res2 == ["mock_dataset"]


def test_get_field_by_dataset_property_with_filter_no_match(
    mock_dataset_json, monkeypatch, get_renkuDataset_List
):
    mock_dataset_json[0]["name"] = "something"

    class MockResponse:
        @staticmethod
        def json():
            return mock_dataset_json

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    res1, res2 = data_commands.get_field_by_dataset_property("mock", filter_ex=True)
    assert res1 == ["XXXXXX"]
    assert res2 == []


def test_get_field_by_dataset_property_no_data(
    mock_dataset_json, monkeypatch, get_renkuDataset_List
):
    class MockResponse:
        @staticmethod
        def json():
            return []

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    res1, res2 = data_commands.get_field_by_dataset_property("mock", filter_ex=True)
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
    mock_dataset_info, monkeypatch, mock_dataset_json
):
    mock_copy = mock_dataset_info.copy()
    mock_copy["name"] = "new"
    info_list = [mock_dataset_info, mock_copy]
    info_list = [mock_dataset_info, mock_dataset_info]

    class MockResponse:
        @staticmethod
        def json():
            return mock_dataset_json

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    uni_dat = data_commands.filter_duplicated_names(info_list)
    assert uni_dat == [mock_dataset_info]


@pytest.mark.api_call
def test_filter_duplicated_names_no_dup(
    mock_dataset_info, monkeypatch, mock_dataset_json
):
    info_list = [mock_dataset_info, mock_dataset_info]

    class MockResponse:
        @staticmethod
        def json():
            return mock_dataset_json

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    uni_dat = data_commands.filter_duplicated_names(info_list)
    assert uni_dat == [mock_dataset_info]


# get_origin_dataset_ids
def test_get_origin_dataset_ids_unique_id(monkeypatch, mock_dataset_info):
    class MockResponse:
        @staticmethod
        def json():
            return mock_dataset_info

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    data_ids = data_commands.get_origin_dataset_ids(["idx"])
    assert data_ids == [mock_dataset_info]


def test_get_origin_dataset_ids_with_sameas(monkeypatch, mock_dataset_info):

    mock_dataset_info["sameAs"] = "idy"

    class MockResponse:
        @staticmethod
        def json():
            return mock_dataset_info

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    data_ids = data_commands.get_origin_dataset_ids(["idx"])
    assert data_ids == [mock_dataset_info]


def test_get_origin_dataset_ids_with_noname(monkeypatch, mock_dataset_info):

    del mock_dataset_info["name"]

    class MockResponse:
        @staticmethod
        def json():
            return mock_dataset_info

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    data_ids = data_commands.get_origin_dataset_ids(["idx"])
    assert data_ids == []


@pytest.mark.api_call
def test_get_origin_dataset_ids_works():
    query_res = data_commands.query_datasets_by_string("test")
    query_id = query_res[0]["identifier"]

    data_ids = data_commands.get_origin_dataset_ids([query_id])
    assert data_ids[0]["name"] == query_res[0]["name"]


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
