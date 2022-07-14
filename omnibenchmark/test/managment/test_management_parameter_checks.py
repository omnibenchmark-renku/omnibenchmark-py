""" All test around the parameter checks"""

from omnibenchmark.management import parameter_checks
import pytest
import re
from omnibenchmark.utils.exceptions import ParameterError


# Test get_all_parameter_combinations
def test_get_all_parameter_combinations_two(mock_param_values):
    param_comb = parameter_checks.get_all_parameter_combinations(mock_param_values)
    assert param_comb[0] == {"param1": 0, "param2": "test"}


def test_get_all_parameter_combinations_one():
    param_comb = parameter_checks.get_all_parameter_combinations(
        values={"param1": [0, 10]}
    )
    assert param_comb == [{"param1": 0}, {"param1": 10}]


def test_get_all_parameter_combinations_multiple(mock_param_values):
    mock_param_values["param3"] = [30, "new_test"]
    param_comb = parameter_checks.get_all_parameter_combinations(mock_param_values)
    assert param_comb[0] == {"param1": 0, "param2": "test", "param3": 30}


def test_get_all_parameter_combinations_none():
    param_comb = parameter_checks.get_all_parameter_combinations(values=None)
    assert param_comb == []


# Test apply_filter
def test_apply_filter_num_bounds():
    value_list = [3, 7, "10", "20", 40, "70"]
    filt = {"lower": 10, "upper": "50", "exclude": 20}
    param_val = parameter_checks.apply_filter(value_list=value_list, filter_vals=filt)
    assert param_val == [10, 40]


def test_apply_filter_filter_list():
    value_list = [3, 7, "10", "20", 40, "70", "test", "another"]
    filt = ["40", 7, "test"]
    param_val = parameter_checks.apply_filter(value_list=value_list, filter_vals=filt)
    assert param_val == [3, "10", "20", "70", "another"]


def test_apply_filter_filter_non_num_bound():
    value_list = [3, "10", 40, "70", "test", "another"]
    filt = {"lower": 10, "upper": "50", "exclude": 20}
    with pytest.raises(ParameterError, match=r"Could not apply filtering of 50*?"):
        parameter_checks.apply_filter(value_list=value_list, filter_vals=filt)


def test_apply_filter_invalid_keys(capsys):
    value_list = [3, 7, "10", "20", 40, "70"]
    filt = {"lower": 10, "upper": "50", "not": 20}
    param_val = parameter_checks.apply_filter(value_list=value_list, filter_vals=filt)
    captured = capsys.readouterr()
    assert param_val == [10, 20, 40]
    assert re.match(r"WARNING: Invalid filter keys.\n*?", captured.out)


# Test filter_parameter
def test_filter_parameter_works(mock_param_values):

    filt = {"param1": {"lower": 5}, "param2": "test"}
    param_val = parameter_checks.filter_parameter(mock_param_values, filter=filt)
    assert param_val == {"param1": [10], "param2": []}


def test_filter_parameter_non_ex_param(mock_param_values, capsys):

    filt = {"param1": {"lower": 5}, "param3": "test"}
    param_val = parameter_checks.filter_parameter(mock_param_values, filter=filt)
    captured = capsys.readouterr()
    assert param_val == {"param1": [10], "param2": ["test"]}
    assert re.match(r"WARNING: Could not find param3*?", captured.out)


def test_filter_parameter_no_filter(mock_param_values):
    param_val = parameter_checks.filter_parameter(mock_param_values, filter=None)
    assert param_val == mock_param_values


# Test filter_parameter_combinations
def test_filter_parameter_combinations_works(mock_combinations):

    filt = {"file": "omnibenchmark/test/managment/ex_filter.json", "upper": "50"}
    param_comb = parameter_checks.filter_parameter_combinations(
        mock_combinations, filter=filt
    )
    assert param_comb == [{"param1": 0, "param2": "test"}]


def test_filter_parameter_combinations_different_formats(mock_combinations):
    mock_combinations[1]["param1"] = "10"
    filt = {"file": "omnibenchmark/test/managment/ex_filter.json", "upper": "50"}
    param_comb = parameter_checks.filter_parameter_combinations(
        mock_combinations, filter=filt
    )
    assert param_comb == [{"param1": 0, "param2": "test"}]
