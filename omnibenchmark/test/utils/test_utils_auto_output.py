from typing import List
import omnibenchmark.utils.auto_output as omni
import pytest

### Test auto output functions

# join_parameter
def test_join_parameter_with_parameter(mock_param):
    test_join = omni.join_parameter(mock_param)
    assert test_join == "param_str_value_str__param_num_10"


def test_join_parameter_without_parameter():
    test_join = omni.join_parameter()
    assert test_join == ""


# join_inputs_parameter
def test_join_inputs_parameter_with_both(mock_param):
    test_join = omni.join_inputs_parameter("test_in", mock_param)
    assert test_join == "test_in__param_str_value_str__param_num_10"


def test_join_inputs_parameter_with_parameter(mock_param):
    test_join = omni.join_inputs_parameter(parameter=mock_param)
    assert test_join == "param_str_value_str__param_num_10"


def test_join_inputs_parameter_with_input():
    test_join = omni.join_inputs_parameter(input="test_in")
    assert test_join == "test_in"


def test_join_inputs_parameter_with_none():
    test_join = omni.join_inputs_parameter()
    assert test_join == ""


# get_out_names_from_input_params
def test_get_out_names_from_input_params_name_out_end(mock_out_end):
    test_out_name = omni.get_out_names_from_input_params(
        name="test_in", output_end=mock_out_end
    )
    assert test_out_name == {
        "red_dim": "data/test_in/test_in__red_dim.mtx.gz",
        "counts": "data/test_in/test_in__counts.json",
    }


def test_get_out_names_from_input_params_remove_dubble_points(mock_out_end):
    mock_out_end["red_dim"] = ".mtx.gz"
    test_out_name = omni.get_out_names_from_input_params(
        name="test_in", output_end=mock_out_end
    )
    assert test_out_name == {
        "red_dim": "data/test_in/test_in__red_dim.mtx.gz",
        "counts": "data/test_in/test_in__counts.json",
    }


def test_get_out_names_from_input_params_name_out_end_parameter(
    mock_out_end, mock_param
):
    test_out_name = omni.get_out_names_from_input_params(
        name="test_in", output_end=mock_out_end, parameter=mock_param
    )
    assert test_out_name == {
        "red_dim": "data/test_in/test_in_param_str_value_str__param_num_10_red_dim.mtx.gz",
        "counts": "data/test_in/test_in_param_str_value_str__param_num_10_counts.json",
    }


def test_get_out_names_from_input_params_new_template(mock_out_end):
    test_out_name = omni.get_out_names_from_input_params(
        name="test_in",
        output_end=mock_out_end,
        out_template="${name}_${out_name}.${out_end}",
    )
    assert test_out_name == {
        "red_dim": "test_in_red_dim.mtx.gz",
        "counts": "test_in_counts.json",
    }


def test_get_out_names_from_input_params_new_tem_vars(mock_out_end):
    test_out_name = omni.get_out_names_from_input_params(
        name="test_in",
        output_end=mock_out_end,
        out_template="${name}_${out_name}_${test_name}.${out_end}",
        test_name="new",
    )
    assert test_out_name == {
        "red_dim": "test_in_red_dim_new.mtx.gz",
        "counts": "test_in_counts_new.json",
    }


def test_get_out_names_from_input_params_invalid_template(mock_out_end):
    with pytest.raises(NameError, match=r"Invalid output filename template: .*?"):
        omni.get_out_names_from_input_params(
            name="test_in",
            output_end=mock_out_end,
            out_template="${quatsch}_${out_name}.${out_end}",
        )


# get_input_file_list
def test_get_input_file_list_with_input(mock_omni_input):
    test_input = omni.get_input_file_list(mock_omni_input)
    assert test_input == ["data1", "data2"]


def test_get_input_file_list_no_input():
    test_input = omni.get_input_file_list()
    assert test_input == []


def test_get_input_file_list_with_none_inputfiles(mock_omni_input):
    mock_omni_input.input_files = None
    test_input = omni.get_input_file_list(mock_omni_input)
    assert test_input == []


# get_parameter_combinations
def test_get_parameter_combinations_with_parameter(
    mock_omni_parameter, mock_combinations
):
    test_param = omni.get_parameter_combinations(parameter=mock_omni_parameter)
    assert test_param == mock_combinations


def test_get_parameter_combinations_no_parameter():
    test_param = omni.get_parameter_combinations()
    assert test_param == []


# get_input_parameter_combinations
def test_get_input_parameter_combinations_none():
    comb = omni.get_input_parameter_combinations()
    assert comb == []


def test_get_input_parameter_combinations_both(mock_omni_parameter, mock_omni_input):
    mock_omni_input.input_files = {
        "data1": {"dim_red_file": "path/to/dim/red", "count_file": "path/to/count"}
    }
    comb = omni.get_input_parameter_combinations(
        parameter=mock_omni_parameter, inputs=mock_omni_input
    )
    assert comb == [
        {
            "input_files": {
                "data1": {
                    "dim_red_file": "path/to/dim/red",
                    "count_file": "path/to/count",
                }
            },
            "parameter": {"param1": 0, "param2": "test"},
            "output_files": None,
        },
        {
            "input_files": {
                "data1": {
                    "dim_red_file": "path/to/dim/red",
                    "count_file": "path/to/count",
                }
            },
            "parameter": {"param1": 10, "param2": "test"},
            "output_files": None,
        },
    ]


def test_get_input_parameter_combinations_parameter(mock_omni_parameter):
    comb = omni.get_input_parameter_combinations(parameter=mock_omni_parameter)
    assert comb == [
        {
            "input_files": None,
            "parameter": {"param1": 0, "param2": "test"},
            "output_files": None,
        },
        {
            "input_files": None,
            "parameter": {"param1": 10, "param2": "test"},
            "output_files": None,
        },
    ]


def test_get_input_parameter_combinations_input(mock_omni_input):
    comb = omni.get_input_parameter_combinations(inputs=mock_omni_input)
    assert comb == [
        {
            "input_files": {
                "data1": {
                    "dim_red_file": "path/to/dim/red",
                    "count_file": "path/to/count",
                }
            },
            "parameter": None,
            "output_files": None,
        },
        {
            "input_files": {
                "data2": {
                    "dim_red_file": "path/to/dim/red2",
                    "count_file": "path/to/count2",
                }
            },
            "parameter": None,
            "output_files": None,
        },
    ]


# get_all_output_combinations
def test_get_all_output_combinations_no_in_param():
    all_out = omni.get_all_output_combinations(
        name="test_out", output_end={"dim_red": "mtx.gz", "counts": "json"}
    )
    assert all_out == [
        {
            "input_files": None,
            "output_files": {
                "dim_red": "data/test_out/test_out__dim_red.mtx.gz",
                "counts": "data/test_out/test_out__counts.json",
            },
            "parameter": None,
        }
    ]


def test_get_all_output_combinations_no_in(mock_omni_parameter):
    all_out = omni.get_all_output_combinations(
        name="test_out", output_end={"dim_red": "mtx.gz"}, parameter=mock_omni_parameter
    )
    assert all_out[0] == {
        "input_files": None,
        "output_files": {
            "dim_red": "data/test_out/test_out_param1_0__param2_test_dim_red.mtx.gz"
        },
        "parameter": {"param1": 0, "param2": "test"},
    }


def test_get_all_output_combinations_no_param(mock_omni_input):
    all_out = omni.get_all_output_combinations(
        name="test_out", output_end={"dim_red": "mtx.gz"}, inputs=mock_omni_input
    )
    assert all_out[0] == {
        "input_files": {
            "count_file": "path/to/count",
            "dim_red_file": "path/to/dim/red",
        },
        "output_files": {"dim_red": "data/test_out/test_out_data1_dim_red.mtx.gz"},
        "parameter": None,
    }


def test_get_all_output_combinations_new_template(mock_omni_input):
    all_out = omni.get_all_output_combinations(
        name="test_out",
        output_end={"dim_red": "mtx.gz"},
        inputs=mock_omni_input,
        out_template="data/${name}/${name}_${unique_values}_${out_name}_${test_name}.${out_end}",
        test_name="new",
    )
    assert all_out[0] == {
        "input_files": {
            "count_file": "path/to/count",
            "dim_red_file": "path/to/dim/red",
        },
        "output_files": {"dim_red": "data/test_out/test_out_data1_dim_red_new.mtx.gz"},
        "parameter": None,
    }


def test_get_all_output_combinations_template_function(mock_omni_input):
    def temp_func(comb):
        temp_val = {}
        if len(list(comb["input_files"].values())[0]) > 1:
            temp_val["in_type"] = "multi"
        else:
            temp_val["in_type"] = "single"
        return temp_val

    all_out = omni.get_all_output_combinations(
        name="test_out",
        output_end={"dim_red": "mtx.gz"},
        inputs=mock_omni_input,
        out_template="data/${name}/${name}_${unique_values}_${out_name}_${in_type}.${out_end}",
        template_fun=temp_func,
    )
    assert all_out[0] == {
        "input_files": {
            "count_file": "path/to/count",
            "dim_red_file": "path/to/dim/red",
        },
        "output_files": {
            "dim_red": "data/test_out/test_out_data1_dim_red_multi.mtx.gz"
        },
        "parameter": None,
    }


def test_get_all_output_combinations_template_fun_vars(
    mock_omni_input, mock_omni_parameter
):
    def temp_func(comb, name_dict):
        data_name = list(comb["input_files"].keys())[0]
        if data_name in name_dict.keys():
            data_name = name_dict[data_name]
        temp_val = {
            "data_name": data_name,
            "param1": comb["parameter"]["param1"],
            "param2": comb["parameter"]["param2"],
        }
        return temp_val

    name_dict = {"data1": "positive_control"}

    all_out = omni.get_all_output_combinations(
        name="test_out",
        output_end={"dim_red": "mtx.gz"},
        inputs=mock_omni_input,
        parameter=mock_omni_parameter,
        out_template="data/${name}/${data_name}_${name}_${param1}_${param2}_${out_name}.${out_end}",
        template_fun=temp_func,
        name_dict=name_dict,
    )
    assert all_out[0]["output_files"] == {
        "dim_red": "data/test_out/positive_control_test_out_0_test_dim_red.mtx.gz"
    }
    assert all_out[2]["output_files"] == {
        "dim_red": "data/test_out/data2_test_out_0_test_dim_red.mtx.gz"
    }


# get_default
def test_get_default_input(mock_omni_input):
    assert omni.get_default(mock_omni_input) == "data1"


def test_get_default_parameter(mock_omni_parameter):
    assert omni.get_default(mock_omni_parameter) == {"param1": "0", "param2": "test"}


def test_get_default_none():
    assert omni.get_default() == []


# get_default_outputs
def test_get_default_outputs_file_mapping(mock_out_mapping):
    mock_out_mapping["input_files"] = None
    mock_out_mapping["parameter"] = None
    default_out = omni.get_default_outputs([mock_out_mapping])
    assert default_out == {"out_file1": "path/to/out1", "out_file2": "path/to/out2"}


def test_get_default_outputs_file_mapping_input(mock_out_mapping, mock_omni_input):
    out_map_all = [mock_out_mapping, mock_out_mapping]
    out_map_all[1]["input_files"] = mock_omni_input.default_files
    out_map_all[1]["output_files"] = {"out_file1": "new_path/to/out1"}
    out_map_all[1]["parameter"] = None
    default_out = omni.get_default_outputs(out_map_all, inputs=mock_omni_input)
    assert default_out == {"out_file1": "new_path/to/out1"}


def test_get_default_outputs_file_mapping_input_param(
    mock_out_mapping, mock_omni_input, mock_omni_parameter
):
    out_map_all = [mock_out_mapping, mock_out_mapping]
    out_map_all[1]["input_files"] = mock_omni_input.default_files
    out_map_all[1]["output_files"] = {"out_file1": "new_path/to/out1"}
    out_map_all[1]["parameter"] = mock_omni_parameter.combinations[0]
    default_out = omni.get_default_outputs(
        out_map_all, inputs=mock_omni_input, parameter=mock_omni_parameter
    )
    assert default_out == {"out_file1": "new_path/to/out1"}
