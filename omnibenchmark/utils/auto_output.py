from typing import Mapping, Optional, List, Union, Callable
from string import Template
import itertools

from omnibenchmark.core.input_classes import OmniInput, OmniParameter, OutMapping
from omnibenchmark.utils.decorators import option_list, option_str
from omnibenchmark.utils.exceptions import InputError
from omnibenchmark.utils.user_input_checks import empty_object_to_none


@option_str
def join_parameter(parameter: Optional[Mapping[str, str]] = None) -> str:

    all_params = "__".join(
        [
            "{}_{}".format(str(param_nam), param_val)
            for param_nam, param_val in zip(
                parameter.keys(), parameter.values()  # type: ignore
            )
        ]
    )
    return all_params


@option_str
def join_inputs_parameter(
    input: Optional[str] = None, parameter: Optional[Mapping[str, str]] = None
) -> str:
    param_str = join_parameter(parameter)
    try:
        if param_str == "":
            joined = "".join([input, param_str])  # type: ignore
        else:
            joined = "__".join([input, param_str])  # type: ignore
    except:
        joined = param_str
    finally:
        return joined


def get_out_names_from_input_params(
    output_end: Mapping[str, str],
    name: str,
    input: Optional[str] = None,
    parameter: Optional[Mapping[str, str]] = None,
    out_template: str = "data/${name}/${name}_${unique_values}_${out_name}.${out_end}",
    **kwargs,
) -> Mapping[str, str]:
    """Generates automatic output file names from inputs and parameters used, based on a template defined in out_template.

    Args:
        input (str): Specific input for this output. Should be potentially uniquely identifyable shortcuts, e.g, dataset names.
        output_end (Mapping[str, str]): Mapping of all output file types and their corresponding endings, e.g. {'norm_counts': 'mtx.gz'}.
        name (str): Name of the method, dataset, etc. the output belongs to.
        parameters (Optional[Mapping[str, str]], optional): Mapping of the parameter an their values used to generate these outputs. Defaults to None.
        out_template (str, optional): Template to generate names from. Defaults to 'data/${name}/${name}__${unique_values}${out_name}.${out_end}'.

    Returns:
        Mapping[str, str]: A mapping of output filetypes and generated names, e.g. '{norm_counts: "data/meth1/meth1__data1__norm_counts.mtx.gz"}'.
    """

    # check template
    valid_keys = ["unique_values", "name", "out_name", "out_end"]
    for arg in kwargs.keys():
        valid_keys.append(arg)
    temp_keys = [
        s[1] or s[2] for s in Template.pattern.findall(out_template) if s[1] or s[2]
    ]
    if any(temp not in valid_keys for temp in temp_keys):
        raise NameError(
            f"Invalid output filename template: {out_template}. Please use valid keys as in {valid_keys} or consider specifying output filenames explicitly."
        )
    unique_values = join_inputs_parameter(input, parameter)
    sub_dict = kwargs
    sub_dict["unique_values"] = unique_values
    sub_dict["name"] = name
    output_names = {}
    for out in output_end.keys():
        out_end = output_end[out]
        sub_dict["out_end"] = out_end
        sub_dict["out_name"] = out
        output_file = Template(out_template).substitute(**sub_dict)
        output_names[out] = output_file.replace("..", ".")

    return output_names


@option_list
def get_input_file_list(inputs: Optional[OmniInput]) -> List:
    return (
        list(inputs.input_files.keys()) if inputs.input_files is not None else []       # type: ignore
    )  


@option_list
def get_parameter_combinations(parameter: Optional[OmniParameter]) -> List:
    return (
        parameter.combinations if parameter.combinations is not None else []             # type: ignore
    )  


@option_list
def get_input_parameter_combinations(
    inputs: Optional[OmniInput] = None, parameter: Optional[OmniParameter] = None
) -> List:
    ins = get_input_file_list(inputs)
    para = get_parameter_combinations(parameter)
    out_list = []

    all_comb = list(itertools.product(ins, para))
    if len(all_comb) >= 1:
        for comb in all_comb:
            out_dict: OutMapping = {
                "output_files": None,
                "input_files": {comb[0]: inputs.input_files[comb[0]]},  # type: ignore
                "parameter": comb[1],
            }
            out_list.append(out_dict)
    else:
        for in_name in ins:
            out_dict_in: OutMapping = {
                "output_files": None,
                "input_files": {in_name: inputs.input_files[in_name]},  # type: ignore
                "parameter": None,
            }
            out_list.append(out_dict_in)
        for para_dict in para:
            out_dict_para: OutMapping = {
                "output_files": None,
                "input_files": None,
                "parameter": para_dict,
            }
            out_list.append(out_dict_para)

    return out_list


def get_template_vars_dependencies(
    comb: OutMapping, fun: Callable[..., Mapping], **kwargs
) -> Mapping:
    return fun(comb, **kwargs)


def get_all_output_combinations(
    name: str,
    output_end: Mapping[str, str],
    inputs: Optional[OmniInput] = None,
    parameter: Optional[OmniParameter] = None,
    out_template: str = "data/${name}/${name}_${unique_values}_${out_name}.${out_end}",
    template_fun: Optional[Callable[..., Mapping]] = None,
    **kwargs,
) -> List[OutMapping]:

    comb_list = get_input_parameter_combinations(inputs=inputs, parameter=parameter)
    out_list = []

    for comb in comb_list:
        if template_fun is not None:
            temp_vars = get_template_vars_dependencies(
                comb=comb, fun=template_fun, **kwargs
            )
        else:
            temp_vars = kwargs
        try:
            input_str = next(iter(comb["input_files"].keys()))
            comb["input_files"] = comb["input_files"][input_str]
        except:
            input_str = None
        finally:
            out_names = get_out_names_from_input_params(
                name=name,
                output_end=output_end,
                input=input_str,
                parameter=comb["parameter"],
                out_template=out_template,
                **temp_vars,
            )
        comb["output_files"] = out_names
        out_list.append(comb)

    if len(out_list) == 0:
        out_names = get_out_names_from_input_params(
            name=name, output_end=output_end, out_template=out_template
        )
        out_map: OutMapping = {
            "output_files": out_names,
            "input_files": None,
            "parameter": None,
        }
        out_list.append(out_map)
    return out_list

@option_list
def convert_values_to_string(d: Optional[Mapping]):
    return {key: str(d[key]) for key in d.keys()}         #type: ignore

@option_list
def get_default(omni_class: Optional[Union[OmniParameter, OmniInput]]):
    default_val = omni_class.default            # type: ignore
    if isinstance(default_val, dict):
        default_val = convert_values_to_string(default_val)
    return default_val  


@option_list
def get_default_input(omni_input: Optional[OmniInput]):
    def_input_nam = omni_input.default  # type: ignore
    if def_input_nam is not None:
        return convert_values_to_string(
            omni_input.input_files[def_input_nam]   # type: ignore
            ) 
    else:
        return []

def check_default_settings(default_inputs: Optional[Mapping], default_outputs: Optional[Mapping], default_params: Optional[Mapping], defaults: OutMapping) -> OutMapping:
    if (
        default_outputs == defaults["output_files"]
        and default_params == convert_values_to_string(defaults["parameter"])
        and default_inputs == convert_values_to_string(defaults["input_files"])
    ): 
        return defaults
    else:
        raise InputError(
            f'Default mappings do not match as expected.\n'
            f'Please check the specified defaults:\n {default_inputs}, {default_outputs}, {default_params}\n.'
            f'Default file mapping:\n {defaults}'
        )


def get_default_outputs(
    file_mapping: List[OutMapping],
    inputs: Optional[OmniInput] = None,
    parameter: Optional[OmniParameter] = None,
) -> Optional[Mapping]:
    def_input = get_default_input(inputs)
    def_param = get_default(parameter)
    def_out = None
    for out_dict in file_mapping:
        if (
            not all(element is None for element in [out_dict["input_files"], out_dict["parameter"]])
            and convert_values_to_string(out_dict["input_files"]) == def_input
            and convert_values_to_string(out_dict["parameter"]) == def_param
        ):
            def_out = out_dict["output_files"]
            def_map = out_dict
    if isinstance(def_out, type(None)):
        def_out = file_mapping[0]["output_files"]
        def_map = file_mapping[0]
    def_map = check_default_settings(default_inputs = def_input, default_outputs= def_out, default_params=def_param, defaults=def_map)
    return def_out


def add_missing_file_map_keys(file_map: OutMapping) -> OutMapping:
    for map_key in ["input_files", "parameter"]:
        if map_key not in file_map.keys():
            file_map[map_key] = None                         # type:ignore
    return file_map

def autocomplete_file_mapping(file_mapping: List[OutMapping]) -> List[OutMapping]:
    return [add_missing_file_map_keys(file_map) for file_map in file_mapping]
