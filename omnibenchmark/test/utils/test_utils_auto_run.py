from omnibenchmark.utils import auto_run as omni
from renku.domain_model.workflow.parameter import CommandParameter, CommandInput


# Test map_plan_names
def test_map_plan_names_empty_plan(mock_plan):
    assert omni.map_plan_names(mock_plan) == {}


def test_map_plan_names_with_all(mock_plan, mock_input, mock_output, mock_parameter):
    mock_plan.inputs = [mock_input]
    mock_plan.outputs = [mock_output]
    mock_plan.parameters = [mock_parameter]
    assert omni.map_plan_names(mock_plan) == {
        "test_input-1": "test/input",
        "test_output-1": "test/output",
        "test_param-1": "test/param",
    }


# Test get_file_type_dict
def test_get_file_type_dict_works(mock_out_mapping):
    assert omni.get_file_type_dict(mock_out_mapping) == {
        "out_file1": "path/to/out1",
        "out_file2": "path/to/out2",
        "in_file1": "path/to/in1",
        "param1": "str_value",
        "param2": 100,
    }


# Test get_file_name_dict
def test_get_file_name_dict_multiple_mapping(mock_file_list):
    assert omni.get_file_name_dict(mock_file_list) == {
        "path/to/dim/red": "dim_red_file",
        "path/to/count": "count_file",
        "0": "param3",
        "test": "param2",
    }


# Test map_plan_names_by_prefix
def test_map_plan_names_by_prefix_with_double(mock_plan):
    mock_param1 = CommandParameter(
        id="AAA", default_value="0", name="param3-3", prefix="param3"
    )
    mock_param2 = CommandParameter(
        id="AAA", default_value="0", name="param1-1", prefix="param1"
    )
    mock_plan.parameters = [mock_param1, mock_param2]
    plan_dict = omni.map_plan_names(mock_plan)
    assert omni.map_plan_names_by_prefix(plan=mock_plan, plan_dict=plan_dict) == {
        "param1": "param1-1",
        "param3": "param3-3",
    }


def test_map_plan_names_by_prefix_without_double(mock_plan, mock_input):
    mock_plan.inputs = [mock_input]
    plan_dict = omni.map_plan_names(mock_plan)
    assert omni.map_plan_names_by_prefix(plan=mock_plan, plan_dict=plan_dict) == {}


def test_map_plan_names_by_prefix_with_double_none(mock_plan):
    mock_param1 = CommandParameter(
        id="AAA", default_value="0", name="param3-3", prefix="param3"
    )
    mock_param2 = CommandParameter(id="AAA", default_value="0", name="param1-1")
    mock_plan.parameters = [mock_param1, mock_param2]
    plan_dict = omni.map_plan_names(mock_plan)
    assert omni.map_plan_names_by_prefix(plan=mock_plan, plan_dict=plan_dict) == {
        "param3": "param3-3"
    }


# Test map_plan_names_file_types
def test_map_plan_names_file_types_duplicates(mock_plan, mock_file_list, mock_input):
    mock_input.default_value = "path/to/dim/red"
    mock_input.name = "dim_red_file-1"
    mock_in2 = CommandInput(
        id="AAA", default_value="path/to/count", name="count_file-1"
    )
    mock_param1 = CommandParameter(
        id="AAA", default_value="0", name="param3-3", prefix="param3"
    )
    mock_param2 = CommandParameter(
        id="AAA", default_value="0", name="param1-1", prefix="param1"
    )
    mock_plan.parameters = [mock_param1, mock_param2]
    mock_plan.inputs = [mock_input, mock_in2]
    mock_file_dict = omni.get_file_name_dict(file_mapping=mock_file_list)
    assert omni.map_plan_names_file_types(plan=mock_plan, file_dict=mock_file_dict) == {
        "count_file": "count_file-1",
        "dim_red_file": "dim_red_file-1",
        "param1": "param1-1",
        "param3": "param3-3",
    }


def test_map_plan_names_file_types_no_match(mock_plan, mock_file_list):
    mock_file_dict = omni.get_file_name_dict(file_mapping=mock_file_list)
    assert (
        omni.map_plan_names_file_types(plan=mock_plan, file_dict=mock_file_dict) == {}
    )


def test_map_plan_names_file_types_not_in_list(mock_plan, mock_file_list):
    mock_in = CommandInput(
        id="AAA", default_value="new/path/to/count", name="new_count_file-1"
    )
    mock_plan.inputs = [mock_in]
    mock_file_dict = omni.get_file_name_dict(file_mapping=mock_file_list)
    assert (
        omni.map_plan_names_file_types(plan=mock_plan, file_dict=mock_file_dict) == {}
    )


# Test get_file_mapping_from_out_files
def test_get_file_mapping_from_out_files_match(mock_out_mapping):
    assert omni.get_file_mapping_from_out_files(
        out_files=["path/to/out1"], file_mapping=[mock_out_mapping]
    ) == [mock_out_mapping]


def test_get_file_mapping_from_out_files_no_match(mock_out_mapping):
    assert (
        omni.get_file_mapping_from_out_files(
            out_files=["new/path/to/out1"], file_mapping=[mock_out_mapping]
        )
        == []
    )


def test_get_file_mapping_from_out_files_no_mapping():
    assert omni.get_file_mapping_from_out_files(out_files=["new/path/to/out1"]) == []


# Test get_file_list_from_out_mapping
def test_get_file_list_from_out_mapping_one(mock_out_mapping):
    assert omni.get_file_list_from_out_mapping([mock_out_mapping]) == [
        "path/to/out1",
        "path/to/out2",
        "path/to/in1",
        "str_value",
        100,
    ]


def test_get_file_list_from_out_mapping_two(mock_out_mapping):
    assert omni.get_file_list_from_out_mapping(
        [mock_out_mapping, mock_out_mapping]
    ) == [
        "path/to/out1",
        "path/to/out2",
        "path/to/in1",
        "str_value",
        100,
        "path/to/out1",
        "path/to/out2",
        "path/to/in1",
        "str_value",
        100,
    ]


# Test get_file_list_from_out_mapping
def test_get_file_list_from_out_mapping_none():
    assert omni.get_file_list_from_out_mapping([]) == []


def test_get_file_list_from_out_mapping_half_empty(mock_out_mapping):
    mock_out_mapping["output_files"] = {}
    assert omni.get_file_list_from_out_mapping([mock_out_mapping]) == [
        "path/to/in1",
        "str_value",
        100,
    ]
