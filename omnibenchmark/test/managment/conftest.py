"""Fixtures related to management functions"""

import pytest
import json


@pytest.fixture
def mock_filter():
    return {
        "param_1": {"upper": 50, "lower": 10},
        "param_2": {"exclude": ["val1", "val3"]},
        "file": "path/to/filter.json",
    }
