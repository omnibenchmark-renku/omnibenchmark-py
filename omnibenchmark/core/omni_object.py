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
    revert_run,
)
from omnibenchmark.management.general_checks import find_orchestrator, is_renku_project
from omnibenchmark.management.data_checks import find_outputs_with_missing_inputs
from omnibenchmark.management.data_commands import (
    update_dataset_files,
    get_data_url_by_keyword,
)
from omnibenchmark.utils.exceptions import InputError

from omnibenchmark.utils.user_input_checks import flatten, rm_none_from_list
from omnibenchmark.management.wflow_checks import (
    check_plan_exist,
    filter_activity_exist,
)
from omnibenchmark.utils.default_global_vars import OmniRenkuInst
from renku.domain_model.dataset import Dataset as RenkuDataSet
from renku.command.view_model.plan import PlanViewModel
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
            command (Optional[OmniCommand], optional): Workflow command, automatically generated if missing. Defaults to None.
            inputs (Optional[OmniInput], optional): Definitions of the workflow inputs. Defaults to None.
            parameter (Optional[OmniParameter], optional): Definitions of the workflow parameter. Defaults to None.
            outputs (Optional[OmniOutput], optional): Definitions of the workflow outputs. Defaults to None.
            omni_plan (Optional[OmniPlan], optional): The workflow description. Defaults to None.
            benchmark_name (Optional[str], optional): Name of the benchmark the module is associated to. Defaults to None.
            orchestrator (Optional[str], optional): Orchestrator url of the benchmark th emodule is associated to.
                                                    Automatic detection. Defaults to None.
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

    def run_renku(self, all: bool = True, provider: str = "toil", config: Optional[str] = None):
        self.command = check_omni_command(self.command, self.script, self.outputs)
        if self.outputs is not None:
            out_files = get_all_output_file_names(self.outputs)
            check_output_directories(out_files)
        self.omni_plan = manage_renku_plan(
            omni_plan=self.omni_plan,
            command=self.command,
            output=self.outputs,
            name=self.wflow_name,
            description=self.description,
        )
        if self.outputs is not None and all:
            manage_renku_activities(
                outputs=self.outputs, omni_plan=self.omni_plan, provider=provider, config=config
            )

    def update_result_dataset(self, clean: bool = True):
        """Add output files to the objects dataset and update the dataset"""
        if self.outputs is None:
            print(
                f"No output files detected. Nothing to update for {self.dataset_name}."
            )
            return
        out_files = get_all_output_file_names(self.outputs)
        update_dataset_files(
            urls=out_files, dataset_name=self.dataset_name  # type:ignore
        )
        renku_dataset_update(names=[self.dataset_name])  # type:ignore
        out_no_input = find_outputs_with_missing_inputs()
        if len(out_no_input) > 0:
            revert_run(
                out_files=out_no_input, dataset_name=self.dataset_name, remove=clean
            )

    def update_object(
        self, check_o_url: bool = True, n_latest: int = 9, all: bool = True
    ):
        """Update the objects inputs, parameter and output definition. Does not run or update workflows/activities.
        Args:
            check_o_url (bool): If linking to an orchestrator shall be checked.
                                WARNING: If False ALL existing datasets with that keyword will be imported!
            n_latest (int): Number of latest pipelines to include into orchestrator checks
        """
        if not check_o_url:
            self.orchestrator = "placeholder/string"
        if self.orchestrator is None:
            if self.benchmark_name is not None:
                self.orchestrator = find_orchestrator(
                    benchmark_name=self.benchmark_name, bench_url=self.BENCH_URL
                )
            if self.orchestrator is None:
                print(
                    f"WARNING: No orchestrator specified! \n"
                    f"No new datasets will be imported. Consider specifying an orchestrator by running:\n"
                    f"OmniObject.orchestrator = find_orchestrator(BENCHMARK_NAME) \n"
                    f"Look at {self.BENCH_URL} to get a list of possible BENCHMARK_NAMEs."
                )
        if self.inputs is not None and self.orchestrator is not None:
            self.inputs.update_inputs(
                orchestrator=self.orchestrator,
                query_url=self.DATA_QUERY_URL,
                data_url=self.DATA_URL,
                gitlab_url=self.GIT_URL,
                check_o_url=check_o_url,
                n_latest=n_latest,
                all=all,
            )
        if self.parameter is not None and self.orchestrator is not None:
            self.parameter.update_parameter(
                orchestrator=self.orchestrator,
                query_url=self.DATA_QUERY_URL,
                data_url=self.DATA_URL,
                gitlab_url=self.GIT_URL,
                check_o_url=check_o_url,
                n_latest=n_latest,
            )
        if self.outputs is not None:
            self.outputs.inputs = self.inputs
            self.outputs.parameter = self.parameter
            self.outputs.update_outputs()

        if self.command is not None:
            self.command.outputs = self.outputs
            self.command.update_command()

    def clean_revert_run(self):
        """Unlink and delete all output files, and revert all activities related to this object and delete the corresponding plan.

        This is intended in cases of overthroughing everything and starting with a clean repository.
        """
        out_files = flatten(
            [list(fi["output_files"].values()) for fi in self.outputs.file_mapping]
        )
        revert_run(out_files=out_files, dataset_name=self.dataset_name)

    def check_updates(self, n_latest: int = 9, check_o_url: bool = True):
        """Shows what inputs are supposed to be updated- and imported upon omni_obj.update_object()

        Args:
            n_latest (int, optional): Number of latest pipelines to check for the orchestrator check. Defaults to 9.
            check_o_url (bool, optional): If the imported datasets have to be part of an orchestrator. Defaults to True.
        """

        imp_list: List = []
        up_list: List = []

        if self.inputs is None:
            print(
                "No inputs defined and no input keyword provided.\n"
                "Nothing will be updated.\n"
                "Consider adding an instance of OmniInput as omni_obj.inputs.\n"
                "Imports will be based on omni_obj.inputs.keywords."
            )
            return
        if self.inputs.keyword is None:
            print(
                "No keyword specified. Nothing to update/import.\n"
                "Please provide a keyword to enable imports in the form of: \n"
                "omni_obj.inputs.keyword = [KEY1, KEY2]"
            )
            return
        if not check_o_url:
            self.orchestrator = "placeholder/string"
        if self.orchestrator is None:
            if self.benchmark_name is not None:
                self.orchestrator = find_orchestrator(
                    benchmark_name=self.benchmark_name, bench_url=self.BENCH_URL
                )
            if self.orchestrator is None:
                print(
                    f"WARNING: No orchestrator specified! \n"
                    f"No new datasets will be imported. Consider specifying an orchestrator by running:\n"
                    f"OmniObject.orchestrator = find_orchestrator(BENCHMARK_NAME) \n"
                    f"Look at {self.BENCH_URL} to get a list of possible BENCHMARK_NAMEs."
                )
                return
        if self.parameter is None:
            keys = self.inputs.keyword
        else:
            keys = flatten(
                [
                    k
                    for k in [self.inputs.keyword, self.parameter.keyword]
                    if k is not None
                ]
            )
        for key in keys:
            imp_ids, up_names = get_data_url_by_keyword(
                keyword=key,
                filter_names=self.inputs.filter_names,
                o_url=self.orchestrator,
                filter_ex=True,
                query_url=self.DATA_QUERY_URL,
                data_url=self.DATA_URL,
                gitlab_url=self.GIT_URL,
                check_o_url=check_o_url,
                n_latest=n_latest,
            )

            imp_list.append(imp_ids)
            up_list.append(up_names)

        imp_list = flatten(imp_list)
        up_list = flatten(up_list)
        nl = "\n"
        if len(imp_list) > 0:
            print(
                f"The following datasets will be imported upon omni_obj.update_object():\n"
                f"{nl}{nl.join(imp_list)}"
            )

        if len(up_list) > 0:
            print(
                f"The following datasets will be updated upon omni_obj.update_object():\n"
                f"{nl}{nl.join(up_list)}"
            )
        else:
            print(
                "No existing dataset matching the specified keyword found. Nothing to be updated"
            )

    def check_run(self):

        self.command = check_omni_command(self.command, self.script, self.outputs)
        out_files = get_all_output_file_names(self.outputs)
        plan = check_plan_exist(out_files)
        nl = "\n"
        if plan is None:
            print(
                "No workflow associated to this object exist.\n"
                "The following command will be run to generate one:\n"
                f"{self.command.command_line}\n"
                "Further outputs will be generated with that workflow:\n"
                f"{nl}{nl.join(out_files)}"
            )
            return
        plan_view = PlanViewModel.from_plan(plan)
        activity_out = filter_activity_exist(out_files)
        activity_out = rm_none_from_list(activity_out)
        no_activity = [out for out in out_files if out not in activity_out]
        print(
            "The following workflow is associated to this object:\n"
            f"Command:\n {plan_view.full_command}\n"
            f"Inputs:\n {[input.__dict__ for input in plan_view.inputs]}\n"
            f"Outputs:\n {[output.__dict__ for output in plan_view.outputs]}\n"
            f"Parameter:\n {[param.__dict__ for param in plan_view.parameters]}\n"
            "Activities for the following outputs exist and will be checked for updates:\n"
            f"{nl}{nl.join(activity_out)}\n"
            "New activities for the following outputs will  be generated:\n"
            f"{nl}{nl.join(no_activity)}"
        )

    def execute_plan_without_KG(
        self, inputs, parameter, outputs, time_out: Optional[int] = None
    ):
        pass
