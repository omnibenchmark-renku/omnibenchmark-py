from omnibenchmark.core.input_classes import OmniInput, OmniParameter
from omnibenchmark.core.output_classes import OmniCommand, OmniOutput
from omnibenchmark.core.omni_object import OmniObject
import omnibenchmark.utils.build_omni_object as omni
from omnibenchmark.utils.exceptions import InputError
from typeguard import check_type
import pytest
import yaml


# Test build_omni_input_from_config_inputs
def test_build_omni_input_from_config_inputs_with_input(mock_config):
    omni_input = omni.build_omni_input_from_config_inputs(mock_config["inputs"])
    assert isinstance(omni_input, OmniInput)
    assert omni_input.names == ["count_file", "dim_red_file"]
    assert omni_input.prefix == {
        "count_file": ["counts"],
        "dim_red_file": ["features", "genes"],
    }
    assert omni_input.default_files == {
        "count_file": "data/import_this_dataset/import_this_dataset__counts.mtx.gz",
        "dim_red_file": "data/import_this_dataset/import_this_dataset__dim_red_file.json",
    }


def test_build_omni_input_from_config_inputs_with_none():
    assert isinstance(
        omni.build_omni_input_from_config_inputs(config_inputs=None), type(None)
    )


def test_build_omni_input_from_config_inputs_no_keyword(mock_config):
    del mock_config["inputs"]["keywords"]
    omni_input = omni.build_omni_input_from_config_inputs(mock_config["inputs"])
    assert isinstance(omni_input, OmniInput)


def test_build_omni_input_from_config_inputs_no_files(mock_config):
    del mock_config["inputs"]["files"]
    omni_input = omni.build_omni_input_from_config_inputs(mock_config["inputs"])
    assert isinstance(omni_input, OmniInput)
    assert omni_input.names == ["count_file", "dim_red_file"]


def test_build_omni_input_from_config_inputs_no_files_pre(mock_config):
    del mock_config["inputs"]["files"]
    del mock_config["inputs"]["prefix"]
    omni_input = omni.build_omni_input_from_config_inputs(mock_config["inputs"])
    assert isinstance(omni_input, OmniInput)


def test_build_omni_input_from_config_inputs_minimal(mock_config):
    del mock_config["inputs"]["input_files"]
    del mock_config["inputs"]["default"]
    omni_input = omni.build_omni_input_from_config_inputs(mock_config["inputs"])
    assert isinstance(omni_input, OmniInput)
    assert omni_input.names == ["count_file", "dim_red_file"]


def test_build_omni_input_from_config_inputs_none(mock_config):
    del mock_config["inputs"]["input_files"]
    del mock_config["inputs"]["prefix"]
    del mock_config["inputs"]["files"]
    omni_input = omni.build_omni_input_from_config_inputs(mock_config["inputs"])
    assert isinstance(omni_input, type(None))


# Test build_omni_parameter_from_config_params
def test_build_omni_parameter_from_config_params_with_params(mock_config):
    assert isinstance(
        omni.build_omni_parameter_from_config_params(mock_config["parameter"]),
        OmniParameter,
    )


def test_build_omni_parameter_from_config_params_none():
    assert isinstance(
        omni.build_omni_parameter_from_config_params(config_params=None), type(None)
    )


def test_build_omni_parameter_from_config_params_no_values(mock_config):
    del mock_config["parameter"]["values"]
    omni_param = omni.build_omni_parameter_from_config_params(mock_config["parameter"])
    assert isinstance(omni_param, OmniParameter)


def test_build_omni_parameter_from_config_params_no_combinations_but_default(mock_config):
    del mock_config["parameter"]["combinations"]
    with pytest.raises(InputError, match=r"No parameter input detected, but default specified*?"):
        omni.build_omni_parameter_from_config_params(mock_config["parameter"])

def test_build_omni_parameter_from_config_params_no_comb_no_def(mock_config):
    del mock_config["parameter"]["combinations"]
    del mock_config["parameter"]["default"]
    omni_param = omni.build_omni_parameter_from_config_params(mock_config["parameter"])
    assert isinstance(omni_param, OmniParameter)


def test_build_omni_parameter_from_config_params_no_default(mock_config):
    del mock_config["parameter"]["default"]
    del mock_config["parameter"]["filter"]
    omni_param = omni.build_omni_parameter_from_config_params(mock_config["parameter"])
    assert isinstance(omni_param, OmniParameter)


def test_build_omni_parameter_from_config_params_no_filter(mock_config):
    del mock_config["parameter"]["filter"]
    omni_param = omni.build_omni_parameter_from_config_params(mock_config["parameter"])
    assert isinstance(omni_param, OmniParameter)


def test_build_omni_parameter_from_config_params_no_key(mock_config):
    del mock_config["parameter"]["keywords"]
    omni_param = omni.build_omni_parameter_from_config_params(mock_config["parameter"])
    assert isinstance(omni_param, OmniParameter)


### Test build_omni_parameter_from_config_params get names
def test_build_omni_parameter_from_config_params_no_names_at_all(mock_config):
    del mock_config["parameter"]["names"]
    del mock_config["parameter"]["combinations"]
    del mock_config["parameter"]["default"]
    del mock_config["parameter"]["values"]
    omni_param = omni.build_omni_parameter_from_config_params(mock_config["parameter"])
    assert isinstance(omni_param, type(None))


def test_build_omni_parameter_from_config_params_names_from_combs(mock_config):
    del mock_config["parameter"]["names"]
    del mock_config["parameter"]["default"]
    del mock_config["parameter"]["values"]
    del mock_config["parameter"]["filter"]
    omni_param = omni.build_omni_parameter_from_config_params(mock_config["parameter"])
    assert isinstance(omni_param, OmniParameter)


def test_build_omni_parameter_from_config_params_names_from_values(mock_config):
    del mock_config["parameter"]["names"]
    del mock_config["parameter"]["default"]
    del mock_config["parameter"]["combinations"]
    del mock_config["parameter"]["filter"]
    omni_param = omni.build_omni_parameter_from_config_params(mock_config["parameter"])
    assert isinstance(omni_param, OmniParameter)


def test_build_omni_parameter_from_config_params_names_from_default(mock_config):
    del mock_config["parameter"]["names"]
    del mock_config["parameter"]["values"]
    del mock_config["parameter"]["combinations"]
    omni_param = omni.build_omni_parameter_from_config_params(mock_config["parameter"])
    assert isinstance(omni_param, OmniParameter)


# Test build_omni_output_from_config
def test_build_omni_output_from_config_with_outputs(mock_config):
    omni_output = omni.build_omni_output_from_config(mock_config)
    assert isinstance(omni_output, OmniOutput)
    assert omni_output.file_mapping[0]["parameter"]["param1"] == 10


def test_build_omni_output_from_config_no_in_params(mock_config):
    del mock_config["parameter"]
    del mock_config["inputs"]
    assert isinstance(omni.build_omni_output_from_config(mock_config), OmniOutput)


def test_build_omni_output_from_config_no_outputs(mock_config):
    del mock_config["parameter"]
    del mock_config["inputs"]
    del mock_config["outputs"]
    assert isinstance(omni.build_omni_output_from_config(mock_config), type(None))


def test_build_omni_output_from_config_no_name(mock_config):
    del mock_config["data"]["name"]
    with pytest.raises(InputError, match=r"Invalid config file:*?"):
        omni.build_omni_output_from_config(mock_config)


def test_build_omni_output_from_config_no_mapping(mock_config):
    del mock_config["parameter"]
    del mock_config["inputs"]
    del mock_config["outputs"]["file_mapping"]
    assert isinstance(omni.build_omni_output_from_config(mock_config), OmniOutput)


# Test build_omni_command_from_config
def test_build_omni_command_from_config_works(mock_config):
    assert isinstance(omni.build_omni_command_from_config(mock_config), OmniCommand)


def test_build_omni_command_from_config_no_command_line(mock_config):
    del mock_config["command_line"]
    omni_com = omni.build_omni_command_from_config(mock_config)
    assert isinstance(omni_com, OmniCommand)


def test_build_omni_command_from_config_no_output(mock_config):
    del mock_config["outputs"]
    omni_com = omni.build_omni_command_from_config(mock_config)
    assert isinstance(omni_com, OmniCommand)


def test_build_omni_command_from_config_no_script(mock_config):
    del mock_config["script"]
    omni_com = omni.build_omni_command_from_config(mock_config)
    assert isinstance(omni_com, type(None))


# Test build_omni_object_from_config
def test_build_omni_object_from_config_works(mock_config):
    omni_obj = omni.build_omni_object_from_config(mock_config)
    assert isinstance(omni_obj, OmniObject)
    assert isinstance(omni_obj.inputs, OmniInput)
    assert isinstance(omni_obj.outputs, OmniOutput)
    assert isinstance(omni_obj.parameter, OmniParameter)


def test_build_omni_object_from_config_no_input(mock_config):
    del mock_config["inputs"]
    omni_obj = omni.build_omni_object_from_config(mock_config)
    assert isinstance(omni_obj, OmniObject)
    assert isinstance(omni_obj.inputs, type(None))


def test_build_omni_object_from_config_no_output(mock_config):
    del mock_config["outputs"]
    omni_obj = omni.build_omni_object_from_config(mock_config)
    assert isinstance(omni_obj, OmniObject)
    assert isinstance(omni_obj.outputs, type(None))


def test_build_omni_object_from_config_no_param(mock_config):
    del mock_config["parameter"]
    omni_obj = omni.build_omni_object_from_config(mock_config)
    assert isinstance(omni_obj, OmniObject)
    assert isinstance(omni_obj.parameter, type(None))


def test_build_omni_object_from_config_minimal(mock_config):
    del mock_config["parameter"]
    del mock_config["inputs"]
    del mock_config["outputs"]
    omni_obj = omni.build_omni_object_from_config(mock_config)
    assert isinstance(omni_obj, OmniObject)


@pytest.mark.api_call
def test_build_omni_object_from_config_no_orchestrator(mock_config):
    del mock_config["orchestrator"]
    omni_obj = omni.build_omni_object_from_config(mock_config)
    assert isinstance(omni_obj, OmniObject)
    assert omni_obj.orchestrator is not None


def test_build_omni_object_from_config_no_orchestrator_bench_name(mock_config):
    del mock_config["orchestrator"]
    del mock_config["benchmark_name"]
    omni_obj = omni.build_omni_object_from_config(mock_config)
    assert isinstance(omni_obj, OmniObject)
    assert omni_obj.orchestrator is None


def test_build_omni_object_from_config_no_name_fails(mock_config):
    del mock_config["data"]
    with pytest.raises(InputError, match=r"Invalid config file:*?"):
        omni_obj = omni.build_omni_object_from_config(mock_config)


def test_build_omni_object_from_config_yaml_template_fun():
    def dummy_fun(com_mapping):
        return com_mapping

    yaml_file = "omnibenchmark/test/utils/ex_config.yaml"
    with open(yaml_file) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    config["outputs"]["template_fun"] = dummy_fun
    check_type("config", config, omni.ConfigDict)
    omni_obj = omni.build_omni_object_from_config(config)
    assert isinstance(omni_obj, OmniObject)


# Test get_omni_object_from_yaml
def test_get_omni_object_from_yaml_works():
    omni_obj = omni.get_omni_object_from_yaml("omnibenchmark/test/utils/ex_config.yaml")
    assert isinstance(omni_obj, OmniObject)


def test_get_omni_object_from_yaml_no_input(monkeypatch, mock_config):
    def return_mock_config(*args, **kwargs):
        m_conf = mock_config
        del m_conf["inputs"]
        return m_conf

    monkeypatch.setattr(yaml, "load", return_mock_config)

    omni_obj = omni.get_omni_object_from_yaml("omnibenchmark/test/utils/ex_config.yaml")
    assert isinstance(omni_obj, OmniObject)


def test_get_omni_object_from_yaml_random_key(monkeypatch, mock_config):
    def return_mock_config(*args, **kwargs):
        m_conf = mock_config
        m_conf["random"] = "something"
        return m_conf

    monkeypatch.setattr(yaml, "load", return_mock_config)
    with pytest.raises(TypeError, match=r"extra key(s)*?"):
        omni_obj = omni.get_omni_object_from_yaml(
            "omnibenchmark/test/utils/ex_config.yaml"
        )


def test_get_omni_object_from_yaml_type_mismatch(monkeypatch, mock_config):
    def return_mock_config(*args, **kwargs):
        m_conf = mock_config
        m_conf["data"]["name"] = 10
        return m_conf

    monkeypatch.setattr(yaml, "load", return_mock_config)
    with pytest.raises(TypeError, match=r"type of dict item*?"):
        omni_obj = omni.get_omni_object_from_yaml(
            "omnibenchmark/test/utils/ex_config.yaml"
        )
