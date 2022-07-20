import logging
from omnibenchmark.core.input_classes import OmniInput, OmniParameter
from omnibenchmark.core.output_classes import OmniCommand, OmniOutput, OmniPlan
from omnibenchmark.renku_commands.datasets import (
    renku_dataset_create,
    renku_dataset_update,
)
from omnibenchmark.management.run_commands import (
    manage_renku_plan,
    manage_renku_activities,
    check_omni_command,
    get_all_output_file_names,
    check_output_directories,
)
from omnibenchmark.management.general_checks import find_orchestrator, is_renku_project
from omnibenchmark.management.data_commands import update_dataset_files
from omnibenchmark.utils.auto_output import get_default, convert_values_to_string
from omnibenchmark.utils.user_input_checks import empty_object_to_none
from omnibenchmark.utils.exceptions import InputError
from omnibenchmark.utils.default_global_vars import OmniRenkuInst
from renku.domain_model.dataset import Dataset as RenkuDataSet
from typing import List, Optional
from os import PathLike


class OmniObject(OmniRenkuInst):

    """OmniBench object

    An Omnibenchmark component.
    """

    def __init__(
        self,
        name: str,
        keyword: Optional[List[str]] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        script: Optional[PathLike] = None,
        command: Optional[OmniCommand] = None,
        inputs: Optional[OmniInput] = None,
        parameter: Optional[OmniParameter] = None,
        outputs: Optional[OmniOutput] = None,
        omni_plan: Optional[OmniPlan] = None,
        benchmark_name: Optional[str] = None,
        orchestrator: Optional[str] = None,
    ):

        self.logger = logging.getLogger("omnibenchmark.OmniObject")
        self.name = name
        self.keyword = keyword
        self.title = title
        self.description = description
        self.command = command
        self.inputs = inputs
        self.outputs = outputs
        self.parameter = parameter
        self.script = script
        self.omni_plan = omni_plan
        self.orchestrator = orchestrator
        self.benchmark_name = benchmark_name
        self.renku: bool = is_renku_project()
        self.kg_url: str = super().KG_URL

        if self.command is None and self.script is not None:
            self.command = OmniCommand(script=self.script, outputs=self.outputs)

        if self.orchestrator is None and self.benchmark_name is not None:
            self.orchestrator = find_orchestrator(
                benchmark_name=self.benchmark_name, bench_url=self.BENCH_URL
            )

    def create_dataset(self) -> RenkuDataSet:
        """create renku-dataset defined by the attributes of the class instance

        Returns:
            RenkuDataSet: An object of class Dataset from renku.core.models.dataset containing the class instances attributes.
        """
        renku_dataset = renku_dataset_create(
            self.name,
            self.kg_url,
            title=self.title,
            description=self.description,
            keyword=self.keyword,
        )
        return renku_dataset

    def run_renku(self):
        self.command = check_omni_command(self.command, self.script, self.outputs)
        out_files = get_all_output_file_names(self.outputs)
        check_output_directories(out_files)
        input_default = empty_object_to_none(convert_values_to_string(self.command.input_val))
        param_default = empty_object_to_none(convert_values_to_string(self.command.parameter_val))
        out_default = empty_object_to_none(get_default(self.command.outputs))
        self.omni_plan = manage_renku_plan(
            out_files=out_files,
            omni_plan=self.omni_plan,
            command=self.command.command_line,
            name=self.name,
            description=self.description,
            default_output=out_default,
            default_input=input_default,
            default_parameter=param_default,
        )
        manage_renku_activities(outputs=self.outputs, omni_plan=self.omni_plan)

    def update_result_dataset(self):
        out_files = get_all_output_file_names(self.outputs)
        update_dataset_files(urls=out_files, dataset_name=self.name)
        renku_dataset_update(names=[self.name])

    def update_object(self):
        if self.orchestrator is None:
            if self.benchmark_name is not None:
                self.orchestrator = find_orchestrator(
                    benchmark_name=self.benchmark_name, bench_url=self.BENCH_URL
                )
            if self.orchestrator is None:
                raise InputError(
                    f"Can not update object without specification of benchmark. \n"
                    f"Please indicate which benchmark this object is associated to by running: \n"
                    f"OmniObject.orchestrator = find_orchestrator(BENCHMARK_NAME) \n"
                    f"Look at {self.BENCH_URL} to get a list of possible BENCHMARK_NAMEs"
                )
        if self.inputs is not None:
            self.inputs.update_inputs(
                orchestrator=self.orchestrator,
                query_url=self.DATA_QUERY_URL,
                data_url=self.DATA_URL,
                gitlab_url=self.GIT_URL,
            )
        if self.parameter is not None:
            self.parameter.update_parameter(
                orchestrator=self.orchestrator,
                query_url=self.DATA_QUERY_URL,
                data_url=self.DATA_URL,
                gitlab_url=self.GIT_URL,
            )
        if self.outputs is not None:
            self.outputs.inputs = self.inputs
            self.outputs.parameter = self.parameter
            self.outputs.update_outputs()

        #return self

    def execute_plan_without_KG(
        self, inputs, parameter, outputs, time_out: Optional[int] = None
    ):
        pass
