"""Fixtures related to utils functions"""

import pytest
from renku.domain_model.dataset import Dataset as RenkuDataset
from renku.domain_model.dataset import DatasetFile as RenkuDatasetFile
from renku.domain_model.entity import Entity
from renku.ui.api.models.dataset import Dataset as ApiDataset
import yaml


@pytest.fixture
def mock_param():
    return {"param_str": "value_str", "param_num": 10}


@pytest.fixture
def mock_out_end():
    return {"red_dim": "mtx.gz", "counts": "json"}


@pytest.fixture
def mock_config():
    with open("omnibenchmark/test/utils/ex_config.yaml") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config


@pytest.fixture
def mock_paramDatasetFile():
    ent = Entity(path="omnibenchmark/test/utils/ex_param.json", checksum="XDFGHJK")
    mock_data_fi = RenkuDatasetFile(entity=ent)
    return mock_data_fi


@pytest.fixture
def mock_paramDataset(mock_paramDatasetFile):
    mock_data = RenkuDataset(name="param_dataset")
    mock_data.keywords = ["mock_param"]
    mock_data.title = "Mock param dataset"
    mock_data.dataset_files = [mock_paramDatasetFile, mock_paramDatasetFile]
    return mock_data


@pytest.fixture
def mock_paramapi_Dataset(mock_paramDataset):
    api_data = ApiDataset()
    api_data = api_data._from_dataset(mock_paramDataset)
    return api_data
