"""Classes related to omnibenchmark outputs"""

from typing import Mapping, List, Optional, Union, Callable
from omnibenchmark.utils.user_input_checks import check_name_matching, flatten
from omnibenchmark.utils.exceptions import OutputError
from omnibenchmark.utils.auto_output import (
    get_all_output_combinations,
    get_default_outputs,
    autocomplete_file_mapping,
    filter_file_mapping_list,
)
from omnibenchmark.utils.auto_run import map_plan_names_file_types
from omnibenchmark.core.input_classes import OmniInput, OmniParameter, OutMapping
from omnibenchmark.utils.auto_command import (
    automatic_command_generation,
    get_interpreter_from_extension,
)
from renku.command.view_model.plan import PlanViewModel
from os import PathLike
import os


class OmniOutput:
    """Class to store metadata of datasets and files that are specified as output in an omnibenchmark project"""

    def __init__(
        self,
        name: str,
        out_names: List[str],
        output_end: Optional[Mapping[str, str]] = None,
        out_template: str = "data/${name}/${name}_${unique_values}_${out_name}.${out_end}",
        file_mapping: Optional[List[OutMapping]] = None,
        inputs: Optional[OmniInput] = None,
        parameter: Optional[OmniParameter] = None,
        default: Optional[Mapping] = None,
        filter_json: Optional[str] = None,
        sort_keys: bool = True,
        template_fun: Optional[Callable[..., Mapping]] = None,
        template_vars: Optional[Mapping] = None,
    ):
        """Class to manage outputs of an omnibenchmark module

        Args:
            name (str): Name that is specific for all outputs. Typically the omnibenchmark module name/OmniObject name
            out_names (List[str]): Names of the output file types
            output_end (Optional[Mapping[str, str]], optional): Endings of the output filetypes. Defaults to None.
            out_template (str, optional): Template to generate output file names.
            file_mapping (Optional[List[OutMapping]], optional): Mapping of input files, parameter values and output files.
                                                                 Defaults to None.
            inputs (Optional[OmniInput], optional): Object specifying all valid inputs. Defaults to None.
            parameter (Optional[OmniParameter], optional): Object speccifying the parameter space. Defaults to None.
            default (Optional[Mapping], optional): Default output files. Defaults to None.
            filter_json(Optional[str], optional): Path to json file with filter combinations. Defaults to None.
            sort_keys(bool): If parameter keys should be sorted alphabetically to generate output names. Defaults to True.
            template_fun (Optional[Callable[..., Mapping]], optional): Function to automatically generate output filenames.
            template_vars (Optional[Mapping], optional): Variables that are used by template_fun. Defaults to None.
        """
        self.name = name
        self.out_names = out_names
        self.output_end = output_end
        self.out_template = out_template
        self.file_mapping = file_mapping
        self.inputs = inputs
        self.parameter = parameter
        self.default = default
        self.filter_json = filter_json
        self.sort_keys = sort_keys
        self.template_fun = template_fun
        self.template_vars = template_vars if template_vars is not None else {}

        if self.file_mapping is None:

            if self.output_end is None:
                raise OutputError(
                    "Undefined outputs. Please specify an output file mapping \n"
                    "or output prefix and output ending to automatically generate one."
                )

            check_name_matching(self.out_names, self.output_end.keys())
            self.file_mapping = get_all_output_combinations(
                name=self.name,
                output_end=self.output_end,
                out_template=self.out_template,
                inputs=self.inputs,
                parameter=self.parameter,
                sort_keys=self.sort_keys,
                template_fun=self.template_fun,
                **self.template_vars,
            )

        self.file_mapping = autocomplete_file_mapping(self.file_mapping)
        self.file_mapping = filter_file_mapping_list(
            file_mapping_list=self.file_mapping,
            inputs=self.inputs,
            parameter=self.parameter,
            filter_json=self.filter_json,
        )

        if self.file_mapping is not None:
            check_name_matching(
                self.out_names,
                flatten(
                    [
                        out_mapping["output_files"].keys()  # type: ignore
                        for out_mapping in self.file_mapping
                    ]
                ),
            )

            if self.default is None:
                self.default = get_default_outputs(
                    file_mapping=self.file_mapping,
                    inputs=self.inputs,
                    parameter=self.parameter,
                )
        if self.default is not None:
            check_name_matching(self.out_names, self.default.keys())

    def update_outputs(self):
        """Update output definitions according to the specified inputs/parameter. Does not update workflows or activities."""
        if self.inputs is not None or self.parameter is not None:
            self.template_vars = (
                self.template_vars if self.template_vars is not None else {}
            )
            new_file_mapping = get_all_output_combinations(
                name=self.name,
                output_end=self.output_end,
                out_template=self.out_template,
                inputs=self.inputs,
                parameter=self.parameter,
                sort_keys=self.sort_keys,
                template_fun=self.template_fun,
                **self.template_vars,
            )
            ex_file_mapping = self.file_mapping if self.file_mapping is not None else []
            all_file_mappings = ex_file_mapping + new_file_mapping
            self.file_mapping = list({str(i): i for i in all_file_mappings}.values())
            self.file_mapping = filter_file_mapping_list(
                file_mapping_list=self.file_mapping,
                inputs=self.inputs,
                parameter=self.parameter,
                filter_json=self.filter_json,
            )

        if self.file_mapping is not None:
            check_name_matching(
                self.out_names,
                flatten(
                    [
                        out_mapping["output_files"].keys()  # type: ignore
                        for out_mapping in self.file_mapping
                    ]
                ),
            )

            omni_outfiles = [file_map["output_files"] for file_map in self.file_mapping]
            if self.default is None or self.default not in omni_outfiles:
                self.default = get_default_outputs(
                    file_mapping=self.file_mapping,
                    inputs=self.inputs,
                    parameter=self.parameter,
                )


class OmniCommand:
    """Class to store metadata and attributes of a command in an omnibenchmark project"""

    def __init__(
        self,
        script: Union[PathLike, str],
        interpreter: Optional[str] = None,
        command_line: Optional[str] = None,
        outputs: Optional[OmniOutput] = None,
        input_val: Optional[Mapping] = None,
        parameter_val: Optional[Mapping] = None,
    ):
        """Initialize an instance of the class OmniCommand

        Args:
            script (Union[PathLike, str]): Path to the script run by the command
            interpreter (str, optional): Interpreter to run the script with. Defaults to None.
            command_line (str, optional): Command line to be run. Defaults to None.
            outputs (OmniOutput, optional): Object specifying all outputs. Defaults to None.
            input_val (Optional[Mapping], optional): Input file tyoes and paths to run the command on. Defaults to None.
            parameter_val (Optional[Mapping], optional): Parameter names and values to run the command with. Defaults to None.
        """
        self.script = script
        self.interpreter = interpreter
        self.command_line = command_line
        self.outputs = outputs
        self.input_val = (input_val,)
        self.parameter_val = parameter_val

        if self.command_line is None:
            if self.outputs is None or self.outputs.file_mapping is None:
                print(
                    "WARNING: No outputs/output file mapping in the current project detected.\n"
                    "Run OmniObject.update_object() to update outputs, inputs and parameter.\n"
                    "Currently this object can not be used to generate a workflow."
                )
            else:
                output_val = self.outputs.default
                self.input_val = next(
                    (
                        out_dict["input_files"]  # type:ignore
                        for out_dict in self.outputs.file_mapping
                        if out_dict["output_files"] == output_val
                    ),
                    None,  # type:ignore
                )
                self.parameter_val = next(
                    (
                        out_dict["parameter"]
                        for out_dict in self.outputs.file_mapping
                        if out_dict["output_files"] == output_val
                    ),
                    None,
                )
                if self.interpreter is None:
                    ext = os.path.splitext(self.script)[1]
                    self.interpreter = get_interpreter_from_extension(ext)

                self.command_line = automatic_command_generation(
                    self.script,
                    interpreter=self.interpreter,
                    inputs=self.input_val,  # type:ignore
                    outputs=output_val,
                    parameters=self.parameter_val,
                )
        # Add command checks!

    def update_command(self):
        """Update command according to the specifed inputs/parameter/output

        Raises:
            InputError: Needs an OmniOutput object or the command line specified.
        """
        if self.outputs is None or self.outputs.file_mapping is None:
            print(
                "WARNING: No outputs/output file mapping in the current project detected.\n"
                "Run OmniObject.update_object() to update outputs, inputs and parameter.\n"
                "Currently this object can not be used to generate a workflow."
            )
        else:
            output_val = self.outputs.default
            self.input_val = next(
                (
                    out_dict["input_files"]  # type:ignore
                    for out_dict in self.outputs.file_mapping
                    if out_dict["output_files"] == output_val
                ),
                None,  # type:ignore
            )
            self.parameter_val = next(
                (
                    out_dict["parameter"]
                    for out_dict in self.outputs.file_mapping
                    if out_dict["output_files"] == output_val
                ),
                None,
            )
            if self.interpreter is None:
                ext = os.path.splitext(self.script)[1]
                self.interpreter = get_interpreter_from_extension(ext)
            self.command_line = automatic_command_generation(
                self.script,
                interpreter=self.interpreter,
                inputs=self.input_val,  # type:ignore
                outputs=output_val,
                parameters=self.parameter_val,
            )


class OmniPlan:
    """Class to store the workflow definition/plan of an Omniobject"""

    def __init__(
        self, plan: PlanViewModel, param_mapping: Optional[Mapping[str, str]] = None
    ):
        """Initialize an instance of the class OmniPlan

        Args:
            plan (PlanViewModel): A plan view model as defined in renku
            param_mapping (Optional[Mapping[str, str]], optional): A mapping between the component names of the plan
                                                                   and the OmniObject. Defaults to None.
        """
        self.plan = plan
        self.param_mapping = param_mapping

    def predict_mapping_from_file_dict(
        self, file_dict: Mapping[str, str]
    ) -> Mapping[str, str]:
        """Predict the corresponding mappings of input/parameter/output as defined in the plan and the OmniObject

        Args:
            file_dict (Mapping[str, str]): input/parameter/output mapping as stored in the OmniObject

        Returns:
            Mapping[str, str]: Mapping between the plan names of input/parameter/outputs and the OmniObject names.
        """
        return map_plan_names_file_types(plan=self.plan, file_dict=file_dict)
