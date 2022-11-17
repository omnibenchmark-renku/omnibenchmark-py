"""Commands related to execute a script with renku workflow/run commands"""

from typing import List, Optional, Union
from omnibenchmark.core.input_classes import OutMapping
from omnibenchmark.utils.auto_run import (
    get_file_mapping_from_out_files,
    get_file_type_dict,
    get_file_name_dict,
)
from renku.domain_model.workflow.plan import Plan as PlanDomainModel
from omnibenchmark.utils.exceptions import InputError, ParameterError
from omnibenchmark.management import wflow_checks as wflow
from omnibenchmark.management.data_commands import unlink_dataset_files
import omnibenchmark.renku_commands.workflows as omni_wflow
from omnibenchmark.utils.auto_output import get_default, convert_values_to_string
from omnibenchmark.utils.user_input_checks import (
    parse_explicit_inputs,
    empty_object_to_none,
    flatten,
)
from omnibenchmark.core.output_classes import OmniCommand, OmniOutput, OmniPlan
from omnibenchmark.renku_commands.general import renku_save
from renku.command.view_model.plan import PlanViewModel
from renku.api import Activity, Plan
import os
from os import PathLike
import logging

logger = logging.getLogger("omnibenchmark.management.run_commands")


def update_activity(out_map: OutMapping):
    """update existing activities

    Args:
        out_map (OutMapping): Output Mapping with the path to update activities for
    """
    if out_map["output_files"] is not None:
        out_paths = list(out_map["output_files"].values())
    else:
        out_paths = None
    omni_wflow.renku_update_activity(paths=out_paths)


def create_activity(out_map: OutMapping, omni_plan: OmniPlan):
    """Run an activity to generate a specific output from a plan

    Args:
        out_map (OutMapping): Output mapping with inputs, parameter and output files
        omni_plan (OmniPlan): plan, workflow description to use

    Raises:
        NameError: All elements from outmapping need to have an unique mapping in the plan
    """
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
    omni_plan: Optional[OmniPlan],
    command: OmniCommand,
    output: Optional[OmniOutput],
    name: Optional[str] = None,
    description: Optional[str] = None,
    keyword: Optional[str] = None,
) -> OmniPlan:
    """Check if a renku plan for a set of output files exist and generate one from default parameter if not.

    Args:
        output (Optional[OmniOutput]): An OmniOutput instance with all output files and their mappimg specified.
        command (OmniCommand): OmniCommand object with command line and outputs specified.
        name (str, optional): Workflow name. Defaults to None.
        description (str, optional): Workflow description. Defaults to None.
        keyword (str, optional): Workflow keyword. Defaults to None.

    Returns:
        OmniPlan: A renku planview model with param_mapping
    """
    if output is None:
        output = command.outputs
    if output is None:
        raise InputError(
            "Please specify outputs to be generated.\n"
            "You can either specify command.outputs or outputs directly"
        )
    out_files = get_all_output_file_names(output)
    plan = wflow.check_plan_exist(out_files)
    if plan is not None:
        plan_view = PlanViewModel.from_plan(plan)

    if plan is None:
        if command.outputs is not output:
            command.outputs = output
            command.update_command()
        if command.command_line is None:
            raise InputError(
                "Can not generate a workflow without command and outputs specified.\n"
                "Please make sure to provide an object of class OmniCommand with outputs specified."
            )
        def_input = parse_explicit_inputs(
            empty_object_to_none(convert_values_to_string(command.input_val))
        )
        def_parameter = parse_explicit_inputs(
            empty_object_to_none(convert_values_to_string(command.parameter_val))
        )
        def_output = parse_explicit_inputs(
            empty_object_to_none(get_default(command.outputs))
        )
        result = omni_wflow.renku_workflow_run(
            command_line=command.command_line,
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
        plan_outs = [plan_out.default_value for plan_out in plan_view.outputs]
        file_mapping_plan = get_file_mapping_from_out_files(
            out_files=plan_outs, file_mapping=output.file_mapping
        )[0]
        file_list = [
            file_map
            for file_map in [
                file_mapping_plan["output_files"],
                file_mapping_plan["input_files"],
                file_mapping_plan["parameter"],
            ]
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
    outputs: Optional[OmniOutput],
) -> OmniCommand:
    """Generate and check a command from a specified script and outputs

    Args:
        command (Optional[OmniCommand]): An Omnicommand object to check
        script (Optional[Union[PathLike, str]]): A script to generate the command for.
        outputs (Optional[OmniOutput]): OmniOutput that is associated to the command.

    Raises:
        InputError: Minimal a script to run the command on needs to be specified.

    Returns:
        OmniCommand: An OmniCommand object
    """
    if command is None:
        if script is None:
            raise InputError(
                "Can not run a command without a specified script. Please specify what script to run."
            )
        command = OmniCommand(script=script, outputs=outputs)
    return command


def get_all_output_file_names(output: OmniOutput) -> List[str]:
    """Get a list of all files specified as outputs

    Args:
        output (OmniOutput): An OmniOutputr object

    Returns:
        List[str]: A list of output file names
    """
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


def manage_renku_activities(outputs: OmniOutput, omni_plan: OmniPlan, save: bool = False):
    """Manage renku activities by updating existing ones and generating new activities for output files without.

    Args:
        outputs (OmniOutput): An OmniOutput object
        omni_plan (OmniPlan): A plan/workflow description with mappings to the output
    """
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
        if save:
            renku_save(message="new activity, no image rebuild")

    for activity in activity_map:
        update_activity(activity)
        if save:
            renku_save(message="update activity, no image rebuild")


def check_output_directories(out_files: List[str]):
    """Check if output directoroes exist and generate them if not

    Args:
        out_files (List[str]): List of output files
    """
    out_dir_list = [os.path.dirname(out_file) for out_file in out_files]
    out_dirs = set(out_dir_list)
    for dir in out_dirs:
        os.makedirs(dir, exist_ok=True)


def revert_run(
    out_files: Optional[List[str]] = None,
    in_files: Optional[List[str]] = None,
    plan_id: Optional[str] = None,
    dataset_name: Optional[str] = None,
    remove: bool = True,
):
    """Remove a plan and revert all associated activities. Basically revert all actions of a specific omni_obj.run_renku().

    Args:
        out_files (Optional[List[str]], optional): Output files associated to the activities to revert. Defaults to None.
        in_files (Optional[List[str]], optional): Input files associated to the activities to revert. Defaults to None.
        plan_id (Optional[str], optional): Plan to revert including all associated activities. Defaults to None.
        dataset_name (Optional[str], optional): Dataset names if outputs shall be unlinked before. Defaults to None.
        remove (bool, optional): Shall output files automatically be deleted. Defaults to True.

    Raises:
        ParameterError: At least one of out_files, in_files or plan id need to be specified
        InputError: Could not find a plan associated to this id.
    """
    if out_files is None and in_files is None and plan_id is None:
        raise ParameterError(
            "Missing out_files, in_files and plan. \n"
            "Please specify at least one of out_files, in_files or plan to be reverted. \n"
        )

    activities = []
    out_fis = []
    if in_files is not None:
        activities = flatten([Activity.filter(input=in_fi) for in_fi in in_files])

    if plan_id is not None:
        renku_plan = [plan for plan in Plan.list() if plan.id in plan_id]
        if len(renku_plan) == 0:
            raise InputError(
                f"Invalid plan_id. Could not find any plan associated with {plan_id} in this project."
            )
        activities = activities + renku_plan[0].activities

    if len(activities) > 0:
        out_fis = flatten(
            [[act_out.path for act_out in act.generated_outputs] for act in activities]
        )

    if out_files is not None:
        activities = activities + flatten(
            [Activity.filter(outputs=out_fi) for out_fi in out_files]
        )
        out_fis = out_fis + out_files

    if len(activities) == 0:
        print(
            f" WARNING: Could not find workflow executions related to your input:\n"
            f"out_files: {out_files}.\n"
            f"in_files: {in_files}.\n"
            f"plan_id: {plan_id}.\n"
            f"Nothing to revert."
        )
        return

    if dataset_name is not None:
        unlink_dataset_files(
            out_files=out_fis, dataset_name=dataset_name, remove=remove
        )

    # revert activities
    activity_ids = list(set([act.id for act in activities]))
    [
        omni_wflow.renku_workflow_revert(activity_id=act_id, plan=True)
        for act_id in activity_ids
    ]
