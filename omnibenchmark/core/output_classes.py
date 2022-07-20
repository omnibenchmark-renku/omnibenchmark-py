"""Classes related to omnibenchmark outputs"""

from typing import Mapping, List, Optional, Union, Callable
from omnibenchmark.utils.user_input_checks import check_name_matching, flatten
from omnibenchmark.utils.exceptions import InputError, OutputError
from omnibenchmark.utils.auto_output import (
    get_all_output_combinations,
    get_default_outputs,
    autocomplete_file_mapping,
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
        template_fun: Optional[Callable[..., Mapping]] = None,
        template_vars: Optional[Mapping] = None,
    ):
        self.name = name
        self.out_names = out_names
        self.output_end = output_end
        self.out_template = out_template
        self.file_mapping = file_mapping
        self.inputs = inputs
        self.parameter = parameter
        self.default = default
        self.template_fun = template_fun
        self.template_vars = template_vars if template_vars is not None else {}

        if self.file_mapping is None:

            if self.output_end is None:
                raise OutputError(
                    f"Undefined outputs. Please specify an output file mapping or output prefix and output ending to automatically generate one."
                )

            check_name_matching(self.out_names, self.output_end.keys())
            self.file_mapping = get_all_output_combinations(  
                name=self.name,
                output_end=self.output_end,
                out_template=self.out_template,
                inputs=self.inputs,
                parameter=self.parameter,
                template_fun=self.template_fun,
                **self.template_vars,
            )
        
        self.file_mapping = autocomplete_file_mapping(self.file_mapping)

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
        if self.inputs is not None or self.parameter is not None:
            self.template_vars = self.template_vars if self.template_vars is not None else {}
            new_file_mapping = get_all_output_combinations( 
                name=self.name,
                output_end=self.output_end,
                out_template=self.out_template,
                inputs=self.inputs,
                parameter=self.parameter,
                template_fun=self.template_fun,
                **self.template_vars,
            )
            ex_file_mapping = self.file_mapping if self.file_mapping is not None else []
            all_file_mappings = ex_file_mapping + new_file_mapping
            self.file_mapping = list({str(i):i for i in all_file_mappings}.values())

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
        #return self


class OmniCommand:
    def __init__(
        self,
        script: Union[PathLike, str],
        interpreter: str = None,
        command_line: str = None,
        outputs: OmniOutput = None,
        input_val: Optional[Mapping] = None,
        parameter_val: Optional[Mapping] = None,
    ):
        self.script = script
        self.interpreter = interpreter
        self.command_line = command_line
        self.outputs = outputs
        self.iput_val = input_val,
        self.parameter_val = parameter_val

        if self.command_line is None:
            if self.outputs is None or self.outputs.file_mapping is None:
                raise InputError(
                    f'Can not infer command without Output definition. Please specify either "command_line" or "outputs".'
                )
            output_val = self.outputs.default
            self.input_val = next(
                (
                    out_dict["input_files"]
                    for out_dict in self.outputs.file_mapping
                    if out_dict["output_files"] == output_val
                ),
                None,
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
                ext = os.path.splitext(script)[1]
                self.interpreter = get_interpreter_from_extension(ext)

            self.command_line = automatic_command_generation(
                self.script,
                interpreter=self.interpreter,
                inputs=self.input_val,
                outputs=output_val,
                parameters=self.parameter_val,
            )
        ## Add command checks!


class OmniPlan:
    def __init__(
        self, plan: PlanViewModel, param_mapping: Optional[Mapping[str, str]] = None
    ):
        self.plan = plan
        self.param_mapping = param_mapping

    def predict_mapping_from_file_dict(
        self, file_dict=Mapping[str, str]
    ) -> Mapping[str, str]:
        return map_plan_names_file_types(plan=self.plan, file_dict=file_dict)
