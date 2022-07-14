"""Checks related to workflow management"""

from os import PathLike
from typing import List, Optional, Union
from omnibenchmark.utils.context_manager import (
    configure_plan_gateway,
    configure_activity_gateway,
)
from renku.infrastructure.gateway.activity_gateway import ActivityGateway
from renku.domain_model.workflow.plan import Plan
from omnibenchmark.utils.exceptions import WorkflowError
from omnibenchmark.management import general_checks
import logging

logger = logging.getLogger("omnibenchmark.management.wflow_checks")

## Activities


def activity_plan_is_valid(
    output: Union[PathLike, str], activity_gateway: ActivityGateway
) -> Optional[Union[PathLike, str]]:
    """Check if there is a valid activity associated to a specifc output path

    Args:
        output (Path): Path to an output file
        activity_gateway(ActivityGateway): Activity gateway with a configured database_dispatcher (See get_database_dispatcher).

    Returns:
        output, if a valid acitivity exists, else None
    """
    all_activities = (
        activity_gateway.get_activities_by_generation(output)
        if general_checks.is_renku_project()
        else []
    )
    valid_activities = [
        act
        for act in all_activities
        if isinstance(act.association.plan.invalidated_at, type(None))
    ]
    return output if len(valid_activities) >= 1 else None


def filter_activity_exist(outputs: List[str]) -> List[Union[PathLike, str, None]]:
    """Checks a list of outputs for existing and valid acitivites

    Args:
        outputs (List[str]): A List of output paths

    Returns:
        List[str]: A list of output paths with valid activities
    """

    activity_gateway = configure_activity_gateway()
    return [
        activity_plan_is_valid(out, activity_gateway=activity_gateway)
        for out in outputs
    ]


## Plans


def get_all_plans() -> List[Plan]:
    """Get all existing plans in a project

    Returns:
        List[Plan]: List with all existing plans
    """
    if not general_checks.is_renku_project():
        return []
    else:
        plan_gateway = configure_plan_gateway()
        return plan_gateway.get_all_plans()


def filter_valid_plans(plans: List[Plan]) -> List[Plan]:
    """Filter a list of plans to contain only those plans that were not invalidated

    Args:
        plans (List[Plan]): A list of renku plans

    Returns:
        List[Plan]: A list of valid renku plans
    """
    return [plan for plan in plans if isinstance(plan.invalidated_at, type(None))]


def get_plan_output_values(plan: Plan) -> List[str]:
    """Get default output values for a renku plan

    Args:
        plan (Plan): A renku plan

    Returns:
        str: The default output value of the renku plan
    """
    return [out_val.default_value for out_val in plan.outputs]


def get_plan_id_from_output(output: str, activity_gateway=ActivityGateway) -> List[str]:
    """Get default output values for a renku plan

    Args:
        plan (Plan): A renku plan

    Returns:
        str: The default output value of the renku plan
    """

    all_activities = (
        activity_gateway.get_activities_by_generation(output)
        if general_checks.is_renku_project()
        else []
    )
    return [act.association.plan.id for act in all_activities]


def find_plan_by_outputs(outputs: List[str]) -> Plan:
    """Find a plan that is related to any paths that are part of a list of output files

    Args:
        outputs (List[str]): List of output files

    Returns:
        Optional[Plan]: Plan to generate one or several of those output files
    """
    plans = get_all_plans()
    valid_plans = filter_valid_plans(plans)
    activity_gateway = configure_activity_gateway()
    out_plan_ids = [
        get_plan_id_from_output(out, activity_gateway=activity_gateway)
        for out in outputs
    ]
    flat_ids = [item for sublist in out_plan_ids for item in sublist]
    return [plan for plan in valid_plans if plan.id in flat_ids]


def check_plan_exist(out_files: List[str]) -> Optional[Plan]:
    """Check if exactly one valid plan exists, that describes generation of one or more of the output files

    Args:
        out_files (List[str]): List of output files to look for associated plans

    Returns:
        Optional[Plan]: If one valid plan can be identified, it will be returned.
    """

    plan = find_plan_by_outputs(out_files)

    if len(plan) > 1:
        raise WorkflowError(
            "Ambiguity: To many plans found associated to output files. Make sure that all old plans have been invalidated or specify the correct plan as input."
        )

    if len(plan) == 1:
        logger.info(f"Plan with id {plan[0].id} and name {plan[0].name} exist")
        return plan[0]
    else:
        return None
