from typing import Mapping, Optional, List, Union, Callable, Any
from string import Template
import itertools
import json

from omnibenchmark.core.input_classes import OmniInput, OmniParameter, OutMapping
from omnibenchmark.utils.decorators import option_list, option_str
from omnibenchmark.utils.user_input_checks import empty_object_to_none
from omnibenchmark.management.parameter_checks import dict_values_to_str


def join_parameter(
    parameter: Optional[Mapping[str, str]] = None, sort_keys: bool = True
) -> str:
    """Get a joined string with all parameter names and their value

    Args:
        parameter (Optional[Mapping[str, str]], optional): Parameter mapping. Defaults to None.

    Returns:
        str: Joined string
    """
    if parameter is None:
        return ""
    param_k = (
        sorted(parameter.keys(), key=lambda x: x.lower())
        if sort_keys
        else parameter.keys()
    )
    all_params = "__".join(
        ["{}_{}".format(str(par_k), parameter[par_k]) for par_k in param_k]
    )
    return all_params


@option_str
def join_inputs_parameter(
    input: Optional[str] = None,
    parameter: Optional[Mapping[str, str]] = None,
    sort_keys: bool = True,
) -> str:
    """Get a joined string of parameter and inputs with their respective values

    Args:
        input (Optional[str], optional): Input types and values. Defaults to None.
        parameter (Optional[Mapping[str, str]], optional): Parameter names and values. Defaults to None.

    Returns:
        str: A joined string
    """
    param_str = join_parameter(parameter, sort_keys=sort_keys)
    try:
        if param_str == "":
            joined = "".join([input, param_str])  # type: ignore
        else:
            joined = "__".join([input, param_str])  # type: ignore
    except Exception:
        joined = param_str
    finally:
        return joined


def get_out_names_from_input_params(
    output_end: Mapping[str, str],
    name: str,
    input: Optional[str] = None,
    parameter: Optional[Mapping[str, str]] = None,
    sort_keys: bool = True,
    out_template: str = "data/${name}/${name}_${unique_values}_${out_name}.${out_end}",
    **kwargs,
) -> Mapping[str, str]:
    """Generates automatic output file names from inputs and parameters used, based on a template defined in out_template.

    Args:
        input (str): Specific input for this output. Should be potentially uniquely identifyable shortcuts, e.g, dataset names.
        output_end (Mapping[str, str]): Mapping of all output file types and their corresponding endings,
                                        e.g. {'norm_counts': 'mtx.gz'}.
        name (str): Name of the method, dataset, etc. the output belongs to.
        parameters (Optional[Mapping[str, str]], optional): Mapping of parameter and the values used to generate these outputs.
                                                            Defaults to None.
        out_template (str, optional): Template to generate names from.

    Returns:
        Mapping[str, str]: A mapping of output filetypes and generated names,
                           e.g. '{norm_counts: "data/meth1/meth1__data1__norm_counts.mtx.gz"}'.
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
            f"Invalid output filename template: {out_template}."
            f"Please use valid keys as in {valid_keys} or consider specifying outputs explicitly."
        )
    unique_values = join_inputs_parameter(input, parameter, sort_keys=sort_keys)
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
    """Get a List with all input file types

    Args:
        inputs (Optional[OmniInput]): An OmniInput object

    Returns:
        List: A list with all input file types
    """
    return (
        list(inputs.input_files.keys())  # type: ignore
        if inputs.input_files is not None  # type: ignore
        else []
    )


@option_list
def get_parameter_combinations(parameter: Optional[OmniParameter]) -> List:
    """Extract parameter combinations as specified in an OmniParameter object

    Args:
        parameter (Optional[OmniParameter]): An OmniParameter object

    Returns:
        List: List with all specified parameter combinations
    """
    return (
        parameter.combinations  # type: ignore
        if parameter.combinations is not None  # type: ignore
        else []
    )


@option_list
def get_input_parameter_combinations(
    inputs: Optional[OmniInput] = None, parameter: Optional[OmniParameter] = None
) -> List:
    """Get a list with all parameter and input combinations as OutFileMapping, but no outputs, yet

    Args:
        inputs (Optional[OmniInput], optional): An OmniInput object. Defaults to None.
        parameter (Optional[OmniParameter], optional): An OmniParameter object. Defaults to None.

    Returns:
        List: _description_
    """
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
    sort_keys: bool = True,
    out_template: str = "data/${name}/${name}_${unique_values}_${out_name}.${out_end}",
    template_fun: Optional[Callable[..., Mapping]] = None,
    **kwargs,
) -> List[OutMapping]:
    """Get OutMappings for all possible input and parameter combinations

    Args:
        name (str): Output name
        output_end (Mapping[str, str]): Mapping of output file types with their corresponding file endings
        inputs (Optional[OmniInput], optional): An OmniInput object. Defaults to None.
        parameter (Optional[OmniParameter], optional): An OmniParameter object. Defaults to None.
        out_template (str, optional): A template to automatically generate output file names. Defaults to "data//__.".
        template_fun (Optional[Callable[..., Mapping]], optional): Function to apply for automatic output file generation.
                                                                   Defaults to None.

    Returns:
        List[OutMapping]: A List of all possible OutMappings
    """
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
        except Exception:
            input_str = None
        finally:
            out_names = get_out_names_from_input_params(
                name=name,
                output_end=output_end,
                input=input_str,
                parameter=comb["parameter"],
                sort_keys=sort_keys,
                out_template=out_template,
                **temp_vars,
            )
        comb["output_files"] = out_names
        out_list.append(comb)

    if len(out_list) == 0:
        out_names = get_out_names_from_input_params(
            name=name,
            output_end=output_end,
            sort_keys=sort_keys,
            out_template=out_template,
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
    return {key: str(d[key]) for key in d.keys()}  # type: ignore


@option_list
def get_default(omni_class: Optional[Union[OmniParameter, OmniInput]]):
    default_val = omni_class.default  # type: ignore
    if isinstance(default_val, dict):
        default_val = convert_values_to_string(default_val)
    return default_val


@option_list
def get_default_input(omni_input: Optional[OmniInput]):
    def_input_nam = omni_input.default  # type: ignore
    if def_input_nam is not None:
        return convert_values_to_string(
            omni_input.input_files[def_input_nam]  # type: ignore
        )
    else:
        return []


def check_default_settings(
    default_inputs: Optional[Mapping],
    default_outputs: Optional[Mapping],
    default_params: Optional[Mapping],
    defaults: OutMapping,
) -> OutMapping:
    """Check if the specified defaults for inputs/parameter/outputs match the specified default OutMapping

    Args:
        default_inputs (Optional[Mapping]): Default inputs
        default_outputs (Optional[Mapping]): Default outputs
        default_params (Optional[Mapping]): Default parameter
        defaults (OutMapping): Default OutMapping

    Raises:
        InputError: Specified defaults need to match.

    Returns:
        OutMapping: Default OutMapping
    """
    if (
        default_outputs == defaults["output_files"]
        and default_params == convert_values_to_string(defaults["parameter"])
        and default_inputs == convert_values_to_string(defaults["input_files"])
    ):
        return defaults
    else:
        print(
            f"WARNING: Default mappings do not match.\n"
            f"If you did not specify defaults, ignore this warning.\n"
            f"Otherwise, please check that your combination is valid.\n"
            f"The following default file mapping is used:\n {defaults}"
        )
        return defaults


def get_default_outputs(
    file_mapping: List[OutMapping],
    inputs: Optional[OmniInput] = None,
    parameter: Optional[OmniParameter] = None,
) -> Optional[Mapping]:
    """Get default outputs from the file mapping and default inputs/parameter

    Args:
        file_mapping (List[OutMapping]): List of OutMappings
        inputs (Optional[OmniInput], optional): An OmniInput object. Defaults to None.
        parameter (Optional[OmniParameter], optional): An OmniParameter object. Defaults to None.

    Returns:
        Optional[Mapping]: Default Output files
    """
    def_input = get_default_input(inputs)
    def_param = get_default(parameter)
    def_out = None
    for out_dict in file_mapping:
        if (
            not all(
                element is None
                for element in [out_dict["input_files"], out_dict["parameter"]]
            )
            and convert_values_to_string(out_dict["input_files"]) == def_input
            and convert_values_to_string(out_dict["parameter"]) == def_param
        ):
            def_out = out_dict["output_files"]
            def_map = out_dict
    if isinstance(def_out, type(None)):
        def_out = file_mapping[0]["output_files"]
        def_map = file_mapping[0]
    def_map = check_default_settings(
        default_inputs=def_input,
        default_outputs=def_out,
        default_params=def_param,
        defaults=def_map,
    )
    return def_out


def add_missing_file_map_keys(file_map: OutMapping) -> OutMapping:
    """Add 'input_files', 'parameter' as keys to OutMapping if they are missing

    Args:
        file_map (OutMapping): OutMapping

    Returns:
        OutMapping: OutMapping with all keys.
    """
    for map_key in ["input_files", "parameter"]:
        if map_key not in file_map.keys():
            file_map[map_key] = None  # type:ignore
    return file_map


def autocomplete_file_mapping(file_mapping: List[OutMapping]) -> List[OutMapping]:
    return [add_missing_file_map_keys(file_map) for file_map in file_mapping]


@option_list
def get_input_param_names(
    in_obj: Optional[Union[OmniInput, OmniParameter]]
) -> List[str]:
    return in_obj.names  # type:ignore


@option_list
def get_keys_list(map: Mapping[str, Any]) -> List[str]:
    return list(map.keys())  # type:ignore


def filter_file_mapping_missing_values(
    file_mapping: OutMapping,
    inputs: Optional[OmniInput] = None,
    parameter: Optional[OmniParameter] = None,
) -> Optional[OutMapping]:
    """Filter incomplete file mappings (e.g., if a file type specified as input is missing)

    Args:
        file_mapping (OutMapping): An OutMapping
        inputs (Optional[OmniInput], optional): An OmniInput object. Defaults to None.
        parameter (Optional[OmniParameter], optional): An OmniParameter object. Defaults to None.

    Returns:
        Optional[OutMapping]: Complete OutMapping
    """
    in_files = get_input_param_names(inputs)
    in_param = get_input_param_names(parameter)
    if any(fi not in get_keys_list(file_mapping["input_files"]) for fi in in_files):
        return None
    elif any(
        param not in get_keys_list(file_mapping["parameter"]) for param in in_param
    ):
        return None
    else:
        return file_mapping


def rm_key(d: Mapping, key: str) -> Mapping:
    new_d = dict(d)
    del new_d[key]
    return new_d


def filter_file_mapping_list_input_param_combinations(
    file_mapping: List[OutMapping], filter_list: Mapping
) -> List[OutMapping]:
    """Filter specific input, parameter combinations from the output file mapping list.

    Args:
        file_mapping (List[OutMapping]): List of Output file mappings
        filter_list (Optional[Mapping], optional): List with combinations to filter.

    Returns:
        List[OutMapping]: Filtered list of OutMappings
    """
    filter_format = [
        {filt_key: dict_values_to_str(filt_val) for filt_key, filt_val in filt.items()}
        for filt in filter_list
    ]

    return [
        comb
        for comb in file_mapping
        if rm_key(
            {
                file_key: dict_values_to_str(file_val)  # type:ignore
                for file_key, file_val in comb.items()
            },
            "output_files",
        )
        not in filter_format
    ]


def filter_file_mapping_list_input_param_combinations_json(
    file_mapping: List[OutMapping], filter_json: Optional[str] = None
) -> List[OutMapping]:
    """Filter specific input, parameter combinations defined in a filter.json file from the output file mapping list.

    Args:
        file_mapping (List[OutMapping]): Mapping between input, output and parameter files
        filter_json (Optional[str], optional): Path to json file with the specified combinations. Defaults to None.

    Returns:
        List[OutMapping]: Filtered list of OutMappings
    """
    try:
        with open(filter_json) as f:  # type:ignore
            filter_list = json.load(f)
    except (FileNotFoundError, TypeError):
        return file_mapping

    return filter_file_mapping_list_input_param_combinations(
        file_mapping=file_mapping, filter_list=filter_list
    )


def filter_file_mapping_list(
    file_mapping_list: List[OutMapping],
    inputs: Optional[OmniInput] = None,
    parameter: Optional[OmniParameter] = None,
    filter_json: Optional[str] = None,
) -> Optional[List[OutMapping]]:
    """Filter list of file mappings for imcomplete mappings

    Args:
        file_mapping_list (List[OutMapping]): List of OutMappings
        inputs (Optional[OmniInput], optional): An OmniInput object. Defaults to None.
        parameter (Optional[OmniParameter], optional): An OmniParameter object. Defaults to None.

    Returns:
        Optional[List[OutMapping]]: List of complete OutMappings
    """
    fi_map_list = [
        filter_file_mapping_missing_values(
            file_mapping=fi_map, inputs=inputs, parameter=parameter
        )
        for fi_map in file_mapping_list
    ]
    res = list(filter(None, fi_map_list))
    res_comb = filter_file_mapping_list_input_param_combinations_json(
        file_mapping=res, filter_json=filter_json
    )
    res_uni = [i for n, i in enumerate(res_comb) if i not in res_comb[n + 1 :]]
    return empty_object_to_none(res_uni)
