from __future__ import annotations

# from typing_extensions import TypedDict, Required
from typing import Callable, Mapping, TypedDict
from omnibenchmark.utils.exceptions import InputError
import yaml
from collections import defaultdict
from omnibenchmark.core.omni_object import OmniObject
from omnibenchmark.core.output_classes import OmniCommand, OmniOutput
from omnibenchmark.core.input_classes import OmniInput, OmniParameter
from os import PathLike
from typing import Any, Optional, List, Union
from omnibenchmark.utils.decorators import option_dict_none, option_dict_list
from omnibenchmark.utils.user_input_checks import flatten, empty_object_to_none
import logging
from typeguard import check_type

logger = logging.getLogger("omnibenchmark.build_object")


# Config definitions:


class ConfigData(TypedDict, total=False):
    name: str
    title: Optional[str]
    description: Optional[str]
    keywords: Optional[Union[str, List[str]]]


class ConfigInput(TypedDict, total=False):
    keywords: Optional[Union[str, List[str]]]
    files: Optional[Union[str, List[str]]]
    prefix: Optional[dict]
    input_files: Optional[dict]
    default: Optional[str]
    filter_names: Optional[Union[str, List[str]]]
    multi_data_matching: Optional[bool]


class ConfigOutput(TypedDict, total=False):
    template: Optional[str]
    files: Optional[Mapping]
    file_mapping: Optional[Mapping]
    default: Optional[Mapping]
    filter_json: Optional[str]
    sort_keys: Optional[str]
    template_fun: Optional[Callable]
    template_vars: Optional[Mapping]


class ConfigParam(TypedDict, total=False):
    # names: Required[List[str]]
    names: List[str]
    keywords: Optional[Union[str, List[str]]]
    default: Optional[Mapping]
    values: Optional[Mapping]
    combinations: Optional[Mapping]
    filter: Optional[Mapping]


class ConfigDict(TypedDict, total=False):
    # data: Required[ConfigData]
    data: ConfigData
    script: Optional[str]
    interpreter: Optional[str]
    command_line: Optional[str]
    benchmark_name: Optional[str]
    orchestrator: Optional[str]
    inputs: Optional[ConfigInput]
    outputs: Optional[ConfigOutput]
    parameter: Optional[ConfigParam]


# Functions to build OmniObjects from yaml/config_dict


@option_dict_none
def get_keys(map: Mapping[str, Any]) -> List[str]:
    return list(map.keys())


@option_dict_list
def get_items(map: Mapping[str, Any]) -> List[tuple]:
    return list(map.items())


@option_dict_list
def get_values(map: Mapping[str, Any]) -> List[tuple]:
    return list(map.values())


def into_list(obj: Union[str, list]) -> list:
    if not isinstance(obj, list):
        obj = [obj]
    return obj


@option_dict_none
def build_omni_input_from_config_inputs(
    config_inputs: ConfigInput,
) -> Optional[OmniInput]:
    """Build an OmniInput object from a ConfigInput dictionary

    Args:
        config_inputs (ConfigInput): A ConfigInput dictionary

    Returns:
        Optional[OmniInput]: An OmniInput object
    """
    inputs: defaultdict = defaultdict(list, config_inputs)
    in_pre = inputs["prefix"]
    in_names = empty_object_to_none(into_list(inputs["files"]))
    prefix = empty_object_to_none(
        {name: into_list(pre) for name, pre in get_items(in_pre)}
    )
    keywords = into_list(inputs["keywords"])
    in_files = empty_object_to_none(inputs["input_files"])
    in_file_types = empty_object_to_none(
        list(set(flatten([list(in1.keys()) for in1 in get_values(in_files)])))
    )
    default_in = empty_object_to_none(inputs["default"])
    filter_names = empty_object_to_none(into_list(inputs["filter_names"]))
    in_names = in_names or get_keys(prefix) or in_file_types
    multi = inputs["multi_data_matching"]
    multi_match = multi if not isinstance(multi, List) else False
    if in_names is not None:
        return OmniInput(
            names=in_names,
            prefix=prefix,
            keyword=keywords,
            input_files=in_files,
            default=default_in,
            filter_names=filter_names,
            multi_data_matching=multi_match,
        )
    else:
        logger.warning(
            "Warning: Skipped inputs because of missing information. Please specify at least names."
        )
        return None


@option_dict_none
def build_omni_parameter_from_config_params(
    config_params: ConfigParam,
) -> Optional[OmniParameter]:
    """Build an OmniParameter object from a ConfigParam dictionary

    Args:
        config_params (ConfigParam): A ConfigParam dictionary

    Returns:
        Optional[OmniParameter]: An OmniParameter object
    """
    params: defaultdict = defaultdict(list, config_params)
    param_names = empty_object_to_none(into_list(params["names"]))
    param_values = empty_object_to_none(params["values"])
    param_combs = empty_object_to_none(
        [vals for vals in get_values(params["combinations"])]
    )
    param_comb_types = empty_object_to_none(
        list(
            set(
                flatten(
                    [list(in1.keys()) for in1 in get_values(params["combinations"])]
                )
            )
        )
    )
    default_params = empty_object_to_none(params["default"])
    param_names = (
        param_names
        or get_keys(param_values)
        or get_keys(default_params)
        or param_comb_types
    )
    keywords = into_list(params["keywords"])
    param_filter = empty_object_to_none(params["filter"])
    if param_names is not None:
        return OmniParameter(
            names=param_names,
            filter=param_filter,
            keyword=keywords,
            values=param_values,
            combinations=param_combs,
            default=default_params,
        )
    else:
        logger.warning(
            "Warning: Skipped parameter because of missing information. Please specify at least names."
        )
        return None


def build_omni_output_from_config(
    config: ConfigDict,
    omni_input: Optional[OmniInput] = None,
    omni_parameter: Optional[OmniParameter] = None,
) -> Optional[OmniOutput]:
    """Build an OmniOutput from a ConfigDict

    Args:
        config (ConfigDict): A ConfigDict
        omni_input (Optional[OmniInput], optional): An OmniInput object. Defaults to None.
        omni_parameter (Optional[OmniParameter], optional): An Omniparameter object. Defaults to None.

    Returns:
        Optional[OmniOutput]: An OmniOutput object.
    """
    config_in: defaultdict = defaultdict(dict, config)
    config_outputs = defaultdict(list, config_in["outputs"])
    out_files = config_outputs["files"]
    out_names = get_keys(out_files)
    out_ends = empty_object_to_none(
        {out_names: vals["end"] for out_names, vals in get_items(out_files)}
    )
    template = config_outputs["template"]
    if len(template) == 0:
        template = "data/${name}/${name}_${unique_values}_${out_name}.${out_end}"
    try:
        name = config_in["data"]["name"]
    except Exception:
        raise (
            InputError(
                f"Invalid config file: {config}\n"
                f"Please provide a config.yaml file with a value for data: name:"
            )
        )
    file_map = config_outputs["file_mapping"]
    file_mapping = empty_object_to_none([vals for vals in get_values(file_map)])
    default_out = empty_object_to_none(config_outputs["default"])
    filter_json = empty_object_to_none(config_outputs["filter_json"])
    sort_keys = (
        True
        if (len(config_outputs["sort_keys"]) == 0)
        else eval(config_outputs["sort_keys"])
    )
    template_fun = config_outputs["template_fun"]
    template_fun = None if isinstance(template_fun, List) else template_fun
    template_vars = empty_object_to_none(config_outputs["template_vars"])

    if not isinstance(out_names, type(None)):
        return OmniOutput(
            name=name,
            out_names=out_names,
            output_end=out_ends,
            out_template=template,
            file_mapping=file_mapping,  # type:ignore
            inputs=omni_input,
            parameter=omni_parameter,
            default=default_out,  # type:ignore
            filter_json=filter_json,  # type:ignore
            sort_keys=sort_keys,
            template_fun=template_fun,
            template_vars=template_vars,  # type:ignore
        )
    else:
        logger.warning(
            "Warning: Skipped outputs because of missing information. Please specify at least output names."
        )
        return None


def build_omni_command_from_config(
    config: ConfigDict, omni_output: Optional[OmniOutput] = None
) -> Optional[OmniCommand]:
    """Build an OmniCommand object from a ConfigDict_

    Args:
        config (ConfigDict): A configDict instance
        omni_output (Optional[OmniOutput], optional): An OmniOutput object. Defaults to None.

    Returns:
        Optional[OmniCommand]: An OmniCommand object
    """
    if omni_output is None:
        omni_output = build_omni_output_from_config(config)
    config_in: defaultdict = defaultdict(list, config)
    obj_script = empty_object_to_none(config_in["script"])
    obj_interpreter = empty_object_to_none(config_in["interpreter"])
    obj_command_line = empty_object_to_none(config_in["command_line"])
    if not isinstance(obj_script, type(None)):
        return OmniCommand(
            script=obj_script,
            interpreter=obj_interpreter,
            command_line=obj_command_line,
            outputs=omni_output,
        )
    else:
        logger.warning(
            "Warning: Skipped command because of missing information. Please specify at least script: script path."
        )
        return None


def build_omni_object_from_config(config: ConfigDict) -> OmniObject:
    """Build an OmniObject from a Config dict instance

    Args:
        config (ConfigDict): A ConfigDict instance.

    Returns:
        OmniObject: An OmniObject object.
    """
    config_in: defaultdict = defaultdict(dict, config)
    omni_input = build_omni_input_from_config_inputs(config_in["inputs"])
    omni_parameter = build_omni_parameter_from_config_params(config_in["parameter"])
    omni_output = build_omni_output_from_config(
        config, omni_input=omni_input, omni_parameter=omni_parameter
    )
    omni_command = build_omni_command_from_config(
        config=config, omni_output=omni_output
    )
    config_data = defaultdict(list, config_in["data"])
    obj_name = empty_object_to_none(config_data["name"])
    obj_key = empty_object_to_none(into_list(config_data["keywords"]))
    obj_title = empty_object_to_none(config_data["title"])
    obj_description = empty_object_to_none(config_data["description"])
    obj_script = empty_object_to_none(config_in["script"])
    obj_bench_name = empty_object_to_none(config_in["benchmark_name"])
    obj_orchestrator = empty_object_to_none(config_in["orchestrator"])

    omni_object = OmniObject(
        name=obj_name,  # type:ignore
        keyword=obj_key,
        title=obj_title,  # type:ignore
        description=obj_description,  # type:ignore
        script=obj_script,
        benchmark_name=obj_bench_name,
        orchestrator=obj_orchestrator,
        inputs=omni_input,
        command=omni_command,
        outputs=omni_output,
        parameter=omni_parameter,
    )
    return omni_object


def get_omni_object_from_yaml(yaml_file: PathLike) -> OmniObject:
    """Build an OmniObject from defenitions of a yaml file

    Args:
        yaml_file (PathLike): Path to yaml file

    Returns:
        OmniObject: An OmniObject object.
    """
    with open(yaml_file) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    check_type(config, ConfigDict)
    return build_omni_object_from_config(config)
