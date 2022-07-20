from omnibenchmark.core.input_classes import OmniInput, OmniParameter
from omnibenchmark.core.output_classes import OmniOutput
import pytest
import requests
from renku.domain_model.dataset import Dataset as RenkuDataset
from renku.domain_model.dataset import DatasetFile as RenkuDatasetFile
from renku.domain_model.entity import Entity
from renku.ui.api.models.dataset import Dataset as ApiDataset
from renku.command.view_model.plan import (
    PlanViewModel,
    CommandInputViewModel,
    CommandOutputViewModel,
    CommandParameterViewModel,
)
from renku.domain_model.workflow.plan import Plan
from renku.domain_model.workflow.parameter import (
    CommandOutput,
    CommandInput,
    CommandParameter,
)
from renku.domain_model.provenance.activity import Activity, Association
from renku.infrastructure.gateway.activity_gateway import ActivityGateway
from omnibenchmark.utils.context_manager import get_database_dispatcher
from omnibenchmark.core.input_classes import OutMapping
import renku.ui.api
import omnibenchmark.management.general_checks


### API related fixtures


@pytest.fixture
def disable_api_calls(monkeypatch):
    def stunted_get():
        raise RuntimeError("Network access not allowed during testing!")

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: stunted_get())


@pytest.fixture
def mock_html_content():
    return b'\n<!doctype html>\n<html>\n<body>\n<table>\n<thead>\n<tr>\n<th>Benchmark_name</th>\n<th>Description</th>\n<th>Orchestrator</th>\n</tr>\n</thead>\n<tbody>\n<tr>\n<td><em>omni_batch</em>, <em>batch_integration</em></td>\n<td>Methods to integrate/correct batch effects in sc-RNA-seq data</td>\n<td><a href="https://renkulab.io/knowledge-graph/projects/omnibenchmark/orchestrator">https://renkulab.io/knowledge-graph/projects/omnibenchmark/orchestrator</a></td>\n</tr>\n<tr>\n<td><em>omni_celltype</em>, ...</td>\n<td></td>\n<td></td>\n</tr>\n</tbody>\n</table>\n</body>\n</html>'


@pytest.fixture
def mock_dataset_json():
    return [
        {
            "_links": [{"rel": "details", "href": "https://this_is_a_mo.ck"}],
            "description": "A mock dataset that does not exoist in real",
            "identifier": "XXXXXX",
            "title": "A mock dataset",
            "name": "mock_dataset",
            "published": {
                "creator": [{"email": "mock.test@mail.com", "name": "Tesuto Mock"}]
            },
            "date": "2021-06-10T07:17:51.817557Z",
            "projectsCount": 0,
            "keywords": ["mock"],
            "images": [],
        }
    ]


@pytest.fixture
def mock_dataset_info():
    return {
        "_links": [
            {
                "rel": "self",
                "href": "https://renkulab.io/knowledge-graph/datasets/asdfghjjkl8765r",
            },
            {
                "rel": "initial-version",
                "href": "https://renkulab.io/knowledge-graph/datasets/asdfghjjkl8765r",
            },
        ],
        "identifier": "asdfghjjkl8765r",
        "name": "mock_dataset",
        "title": "mock dataset info",
        "url": "https://renkulab.io/datasets/asdfghjjkl8765r",
        "derivedFrom": "https://renkulab.io/datasets/asdfghjjkl8765r",
        "versions": {"initial": "assfsadfel8765r"},
        "description": "something to mock",
        "published": {
            "creator": [
                {"name": "Michael Mustermann", "email": "michi.mustermann@test.com"}
            ]
        },
        "created": "2022-05-25T13:54:51Z",
        "hasPart": [
            {"atLocation": "data/mock_dataset/counts_test.mtx.gz"},
            {"atLocation": "data/mock_dataset/data_info_test.json"},
        ],
        "project": {
            "_links": [
                {
                    "rel": "project-details",
                    "href": "https://renkulab.io/knowledge-graph/projects/mock/data_info",
                }
            ],
            "path": "mock/data_info",
            "name": "data_info",
        },
        "usedIn": [
            {
                "_links": [
                    {
                        "rel": "project-details",
                        "href": "https://renkulab.io/knowledge-graph/projects/mock/data_info",
                    }
                ],
                "path": "mock/data_info",
                "name": "data_info",
            }
        ],
        "keywords": ["mock"],
        "images": [],
    }


@pytest.fixture
def mock_response_json(mock_dataset_json):
    class MockResponse:
        @staticmethod
        def json():
            return mock_dataset_json

    return MockResponse()


@pytest.fixture
def mock_dataset_query(monkeypatch, mock_response_json):
    def get_mock_data_json():
        mock_res = mock_response_json
        return mock_res

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: get_mock_data_json())


### Dataset related fixtures
@pytest.fixture
def mock_renkuDatasetFile():

    ent = Entity(path="some/path/to/genes_file.txt", checksum="XDFGHJK")
    mock_data_fi = RenkuDatasetFile(entity=ent)
    return mock_data_fi


@pytest.fixture
def mock_renkuDataset(mock_renkuDatasetFile):

    mock_data = RenkuDataset(name="mock_dataset")
    mock_data.keywords = ["mock"]
    mock_data.title = "This is a mock dataset and does not exist on the KG"
    mock_data.dataset_files = [mock_renkuDatasetFile]
    return mock_data


@pytest.fixture
def mock_api_Dataset(mock_renkuDataset):

    api_data = ApiDataset()
    api_data = api_data._from_dataset(mock_renkuDataset)
    return api_data


@pytest.fixture
def get_renkuDataset_List(monkeypatch, mock_renkuDataset):
    def get_mock_list():
        return [mock_renkuDataset]

    monkeypatch.setattr(
        renku.ui.api.models.dataset.Dataset,
        "list",
        lambda *args, **kwargs: get_mock_list(),
    )


@pytest.fixture
def no_project_context(monkeypatch):
    def no_renku_project_context():
        return False

    monkeypatch.setattr(
        omnibenchmark.management.general_checks,
        "is_renku_project",
        lambda *args, **kwargs: no_renku_project_context(),
    )


### Activity related fixtures


@pytest.fixture
def act_gateway():

    database_dispatcher = get_database_dispatcher()
    activity_gateway = ActivityGateway()
    activity_gateway.database_dispatcher = database_dispatcher
    return activity_gateway


@pytest.fixture
def mock_input_view():

    input = CommandInputViewModel(name="input1", default_value="this/is/a/default")
    return input


@pytest.fixture
def mock_output_view():

    output = CommandOutputViewModel(
        name="output1", default_value="this/is/another/default"
    )
    return output


@pytest.fixture
def mock_param_view():

    param = CommandParameterViewModel(
        name="param1", default_value="this/is/yet/another/default"
    )
    return param


@pytest.fixture
def mock_plan_view(mock_param_view, mock_input_view, mock_output_view):

    plan = PlanViewModel(
        id="XXX",
        full_command="test command",
        name="test",
        inputs=[mock_input_view],
        outputs=[mock_output_view],
        parameters=[mock_param_view],
    )
    return plan


@pytest.fixture
def mock_plan():

    plan = Plan(id="XXX", command="test command")
    return plan


@pytest.fixture
def mock_activity(mock_plan):

    association = Association(id="YYY", plan=mock_plan, agent="Almut Luetge")
    act = Activity(
        id="YYY",
        association=association,
        ended_at_time="2013-05-24T23:59:59",
        started_at_time="2013-05-24T23:52:59",
        agents=["Almut Luetge"],
    )
    return act


@pytest.fixture
def mock_output():

    output = CommandOutput(id="ZZZ", default_value="test/output", name="test_output-1")
    return output


@pytest.fixture
def mock_input():

    input = CommandInput(id="AAA", default_value="test/input", name="test_input-1")
    return input


@pytest.fixture
def mock_parameter():

    param = CommandParameter(id="AAA", default_value="test/param", name="test_param-1")
    return param


### Output/Input related fixtures
@pytest.fixture
def mock_prefix():
    return {"count_file": "counts", "dim_red_file": ["features", "genes"]}


@pytest.fixture
def mock_inputfiles():
    return {
        "data1": {"dim_red_file": "path/to/dim/red", "count_file": "path/to/count"},
        "data2": {"dim_red_file": "path/to/dim/red2", "count_file": "path/to/count2"},
    }


@pytest.fixture
def mock_omni_input(mock_inputfiles):
    input_obj = OmniInput(
        names=["dim_red_file", "count_file"], input_files=mock_inputfiles
    )
    return input_obj


@pytest.fixture
def mock_param_values():
    return {"param1": [0, 10], "param2": ["test"]}


@pytest.fixture
def mock_combinations():
    return [{"param1": 0, "param2": "test"}, {"param1": 10, "param2": "test"}]


@pytest.fixture
def mock_omni_parameter(mock_param_values, mock_combinations):
    param_obj = OmniParameter(
        names=["param1", "param2"],
        values=mock_param_values,
        combinations=mock_combinations,
    )
    return param_obj


# Omni output related fixtures


@pytest.fixture
def mock_out_mapping():
    map: OutMapping = {
        "output_files": {"out_file1": "path/to/out1", "out_file2": "path/to/out2"},
        "input_files": {"in_file1": "path/to/in1"},
        "parameter": {"param1": "str_value", "param2": 100},
    }

    return map


@pytest.fixture
def mock_plan_dict():
    map = {
        "out_file1": "out-1",
        "out_file2": "out-2",
        "in_file1": "in-1",
        "param1": "param-1",
        "param2": "param-2",
    }

    return map


@pytest.fixture
def mock_omni_output(mock_out_mapping, mock_omni_parameter, mock_omni_input):
    mock_out_mapping["input_files"] = mock_omni_input.input_files[mock_omni_input.default]
    mock_out_mapping["parameter"] = mock_omni_parameter.default
    omni_out = OmniOutput(
        name="mock_res",
        out_names=["out_file1", "out_file2"],
        file_mapping=[mock_out_mapping],
        inputs=mock_omni_input,
        parameter=mock_omni_parameter
    )
    return omni_out


@pytest.fixture
def mock_file_list(mock_combinations, mock_inputfiles):
    param = mock_combinations[0]
    param["param3"] = 0
    return [mock_inputfiles["data1"], param]
