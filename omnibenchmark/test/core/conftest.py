"""Fixtures related to core classes"""

from omnibenchmark.core.input_classes import OutMapping
import pytest


@pytest.fixture
def mock_out_mapping():
    map: OutMapping = {
        "output_files": {"out_file1": "path/to/out1", "out_file2": "path/to/out2"},
        "input_files": {"in_file1": "path/to/in1"},
        "parameter": {"param1": "str_value", "param2": 100},
    }

    return map
