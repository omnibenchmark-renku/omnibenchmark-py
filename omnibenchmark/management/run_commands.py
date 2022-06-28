"""Commands related to execute a script with renku workflow/run commands"""

from typing import List, Mapping, Optional, Union
from omnibenchmark.core.input_classes import OutMapping
from omnibenchmark.utils.auto_run import (
    get_file_mapping_from_out_files,
    get_file_type_dict,
    get_file_name_dict,
)
from renku.domain_model.workflow.plan import Plan
from omnibenchmark.utils.exceptions import InputError
from omnibenchmark.management import wflow_checks as wflow
import omnibenchmark.renku_commands.workflows as omni_wflow
from omnibenchmark.utils.user_input_checks import parse_explicit_inputs, flatten
from omnibenchmark.core.output_classes import OmniCommand, OmniOutput, OmniPlan
from renku.command.view_model.plan import PlanViewModel
import os
from os import PathLike
import logging

logger = logging.getLogger("omnibenchmark.management.run_commands")


def update_activity(out_map: OutMapping):
    if out_map["output_files"] is not None:
        out_paths = list(out_map["output_files"].values())
    else:
        out_paths = None
    omni_wflow.renku_update_activity(paths=out_paths)


def create_activity(out_map: OutMapping, omni_plan: OmniPlan):
    plan = omni_plan.plan
    map_dict = omni_plan.param_mapping
    file_dict = get_file_type_dict(out_map)
    if map_dict is None or any(
        file_type not in list(map_dict.keys()) for file_type in list(file_dict.keys())
    ):
        raise NameError(
            f"Could not assign all workflow items from: ${omni_plan.param_mapping}."
            f'Please check "renku workflow show ${plan.name}".'
            f"Update OmniObject.omni_plan.param_mapping accordingly."
        )
    params = [
        map_dict[str(file_type)] + "=" + str(file_path)
        for file_type, file_path in file_dict.items()
    ]
    workflow = omni_wflow.renku_workflow_execute(name_or_id=plan.id, set_params=params)
    return workflow


def manage_renku_plan(
    out_files: List[str],
    omni_plan: Optional[OmniPlan],
    command: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    keyword: Optional[str] = None,
    default_output: Optional[Mapping] = None,
    default_input: Optional[Mapping] = None,
    default_parameter: Optional[Mapping] = None,
) -> Plan:
    """Check if a renku plan for a set of output files exist and generate one from default parameter if not.

    Args:
        out_files (List[str]): All potential output files
        command_line (str): Command line command to generate default plan.
        name (str, optional): Workflow name. Defaults to None.
        description (str, optional): Workflow description. Defaults to None.
        keyword (str, optional): Workflow keyword. Defaults to None.
        default_output (Optional[Mapping[str, Optional[str]]], optional): Default outputs. Defaults to None.
        default_input (Optional[Mapping[str, Optional[str]]], optional): Default inputs. Defaults to None.
        default_parameter (Optional[Mapping[str, Optional[str]]], optional): Default parameter. Defaults to None.

    Returns:
        Plan: A renku plan object.
    """

    plan = wflow.check_plan_exist(out_files)
    if plan is not None:
        plan_view = PlanViewModel.from_plan(plan)
    def_input = parse_explicit_inputs(default_input)
    def_output = parse_explicit_inputs(default_output)
    def_parameter = parse_explicit_inputs(default_parameter)

    if plan is None:
        result = omni_wflow.renku_workflow_run(
            command_line=command,
            name=name,
            description=description,
            keyword=keyword,
            explicit_inputs=def_input,
            explicit_parameters=def_parameter,
            explicit_outputs=def_output,
        )

        plan_view = result.output

    if omni_plan is None or not plan_view == omni_plan.plan:
        omni_plan = OmniPlan(plan=plan_view)
        file_list = [
            file_map
            for file_map in [default_output, default_input, default_parameter]
            if file_map is not None
        ]
        file_dict = get_file_name_dict(file_mapping=file_list)
        omni_plan.param_mapping = omni_plan.predict_mapping_from_file_dict(
            file_dict=file_dict
        )

    return omni_plan


def check_omni_command(
    command: Optional[OmniCommand],
    script: Optional[Union[PathLike, str]],
    outputs=Optional[OmniOutput],
) -> OmniCommand:
    if command is None:
        if script is None:
            raise InputError(
                f"Can not run a command without a specified script. Please specify what script to run."
            )
        command = OmniCommand(script=script, outputs=outputs)
    return command


def get_all_output_file_names(output: OmniOutput) -> List[str]:
    if output.file_mapping is not None:
        return flatten(
            [
                list(fi_mapping["output_files"].values())
                for fi_mapping in output.file_mapping
                if fi_mapping["output_files"] is not None
            ]
        )
    else:
        return []


def manage_renku_activities(outputs: OmniOutput, omni_plan: OmniPlan):
    # Manage activities
    out_files = get_all_output_file_names(outputs)
    activity_out = wflow.filter_activity_exist(out_files)
    activity_map = get_file_mapping_from_out_files(
        out_files=activity_out, file_mapping=outputs.file_mapping
    )
    if outputs.file_mapping is None:
        outputs.file_mapping = []

    no_activities = [out for out in outputs.file_mapping if out not in activity_map]

    for out_map in no_activities:
        create_activity(out_map, omni_plan)

    for activity in activity_map:
        update_activity(activity)


def check_output_directories(out_files: List[str]):
    out_dir_list = [os.path.dirname(out_file) for out_file in out_files]
    out_dirs = set(out_dir_list)
    for dir in out_dirs:
        os.makedirs(dir, exist_ok=True)
