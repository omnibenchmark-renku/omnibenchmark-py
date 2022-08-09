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

    An Omnibenchmark component. Class to store metadata, inputs, outputs and parameter of an omnibenchmark project.
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
        wflow_name: Optional[str] = None,
        dataset_name: Optional[str] = None,
    ):
        """An object to manage an omnibenchmark module

        Args:
            name (str): Module name 
            keyword (Optional[List[str]], optional): Keyword associated to the modules output dataset. Defaults to None.
            title (Optional[str], optional): Title of the modules output dataset. Defaults to None.
            description (Optional[str], optional): Description of the modules output dataset. Defaults to None.
            script (Optional[PathLike], optional): Script to generate the modules workflow for. Defaults to None.
            command (Optional[OmniCommand], optional): Workflow command - will be automatically generated if missing. Defaults to None.
            inputs (Optional[OmniInput], optional): Definitions of the workflow inputs. Defaults to None.
            parameter (Optional[OmniParameter], optional): Definitions of the workflow parameter. Defaults to None.
            outputs (Optional[OmniOutput], optional): Definitions of the workflow outputs. Defaults to None.
            omni_plan (Optional[OmniPlan], optional): The workflow description. Defaults to None.
            benchmark_name (Optional[str], optional): Name of the benchmark the module is associated to. Defaults to None.
            orchestrator (Optional[str], optional): Orchestrator url of the benchmark th emodule is associated to. Automatic detection. Defaults to None.
            wflow_name (Optional[str], optional): Workflow name. Will be set to the module name if none. Defaults to None.
            dataset_name (Optional[str], optional): Dataset name. Will be set to the module name if none. Defaults to None.
        """
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
        self.wflow_name = wflow_name
        self.dataset_name = dataset_name
        self.renku: bool = is_renku_project()
        self.kg_url: str = super().KG_URL

        if self.command is None and self.script is not None:
            self.command = OmniCommand(script=self.script, outputs=self.outputs)

        if self.orchestrator is None and self.benchmark_name is not None:
            self.orchestrator = find_orchestrator(
                benchmark_name=self.benchmark_name, bench_url=self.BENCH_URL
            )

        if self.wflow_name is None:
            self.wflow_name = self.name

        if self.dataset_name is None:
            self.dataset_name = self.name

    def create_dataset(self) -> RenkuDataSet:
        """create renku-dataset defined by the attributes of the class instance

        Returns:
            RenkuDataSet: An object of class Dataset from renku.core.models.dataset containing the class instances attributes.
        """
        renku_dataset = renku_dataset_create(
            self.dataset_name,  # type:ignore
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
        input_default = empty_object_to_none(
            convert_values_to_string(self.command.input_val)
        )
        param_default = empty_object_to_none(
            convert_values_to_string(self.command.parameter_val)
        )
        out_default = empty_object_to_none(get_default(self.command.outputs))
        self.omni_plan = manage_renku_plan(
            out_files=out_files,
            omni_plan=self.omni_plan,
            command=self.command.command_line,
            name=self.wflow_name,
            description=self.description,
            default_output=out_default,
            default_input=input_default,
            default_parameter=param_default,
        )
        manage_renku_activities(outputs=self.outputs, omni_plan=self.omni_plan)

    def update_result_dataset(self):
        """Add output files to the objects dataset and update the dataset
        """
        out_files = get_all_output_file_names(self.outputs)
        update_dataset_files(urls=out_files, dataset_name=self.dataset_name)
        renku_dataset_update(names=[self.dataset_name])

    def update_object(self):
        """Update the objects inputs, arameter and output definition. Does not run or update workflows/activities.

        Raises:
            InputError: Only runs when an orchestrator url is specified and the object can be associated to an existing benchmark.
        """
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

        if self.command is not None:
            self.command.outputs = self.outputs
            self.command.update_command()

    def execute_plan_without_KG(
        self, inputs, parameter, outputs, time_out: Optional[int] = None
    ):
        pass
