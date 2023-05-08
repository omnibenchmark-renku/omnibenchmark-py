"""Renku workflow commands"""

from __future__ import annotations
from typing import List, Optional
from omnibenchmark.core.input_classes import PathLike
from renku.command.run import run_command_line_command
from renku.command.workflow import execute_workflow_command, revert_activity_command
from renku.command.update import update_command
from renku.command.command_builder.command import CommandResult
from renku.core import errors
from renku.core.util.metadata import construct_creators
from renku.command.format.activity import tabulate_activities
from renku.core.workflow.execute import execute_workflow_graph
from renku.command.command_builder.command import Command
from omnibenchmark.management.general_checks import is_renku_project
from networkx import DiGraph
import logging

logger = logging.getLogger("omnibenchmark.renku_commands")


def renku_workflow_run(
    command_line: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    keyword: Optional[str] = None,
    success_codes: Optional[List[int]] = None,
    explicit_inputs: List = [],
    explicit_outputs: List = [],
    explicit_parameters: List = [],
    no_output: bool = False,
    no_input_detection: bool = False,
    no_output_detection: bool = False,
    creators: Optional[List[str]] = None,
) -> CommandResult:
    """Run a renku workflow

    Args:
        command_line (str): Command to run
        name (str, optional): Workflow name. Defaults to None.
        description (str, optional): Workflow description. Defaults to None.
        keyword (str, optional): Workflow keyword. Defaults to None.
        success_codes (List[int], optional): List of accepted auccess codes. Defaults to None.
        explicit_inputs (List, optional): Explicit input file paths. Defaults to [].
        explicit_outputs (List, optional): Explicit output file paths. Defaults to [].
        explicit_parameters (List, optional): Explicit parameter. Defaults to [].
        no_output (bool, optional): Workflow does not generate outputs. Defaults to False.
        no_input_detection (bool, optional): Turn automatic input detection off. Defaults to False.
        no_output_detection (bool, optional): Turn automatic output detection off. Defaults to False.
    """
    if not is_renku_project():
        logger.error(
            "Project is not a renku project. No workflow generated, consider to running your command without renku."
        )
        return

    if creators:
        creators, _ = construct_creators(creators)

    workflow = (
        run_command_line_command()
        .build()
        .execute(
            name=name,
            description=description,
            keyword=keyword,
            explicit_inputs=explicit_inputs,
            explicit_outputs=explicit_outputs,
            explicit_parameters=explicit_parameters,
            no_output=no_output,
            no_input_detection=no_input_detection,
            no_output_detection=no_output_detection,
            success_codes=success_codes,
            command_line=command_line,
            creators=creators,
        )
    )

    return workflow


def renku_workflow_execute(
    name_or_id: str,
    set_params: List[str],
    provider: str = "toil",
    config: Optional[str] = None,
    values: Optional[str] = None,
    skip_metadata_update: bool = False,
):
    """Execute an existing renku workflow with a specific input/parameter/output combination

    Args:
        name_or_id (str): Workflow name or id
        set_params (List[str]): List of the parameter/inputs/outputs values to use
        provider (str, optional): Provider to run the workflow. Defaults to "cwltool".
        config (Optional[str], optional):Config file for the provider. Defaults to None.
        values (Optional[str], optional): Values for the provider to use. Defaults to None.
        skip_metadata_update (bool, optional): Do not update the workflow metadata. Defaults to False.

    Returns:
        _type_: _description_
    """
    workflow = (
        execute_workflow_command(skip_metadata_update=skip_metadata_update)
        .build()
        .execute(
            name_or_id=name_or_id,
            set_params=set_params,
            provider=provider,
            config=config,
            values=values,
        )
    )
    return workflow


def renku_update_activity(
    update_all: bool = False,
    paths: Optional[List[PathLike]] = None,
    dry_run: bool = False,
    provider: str = "toil",
    ignore_deleted: bool = True,
    config: Optional[str] = None,
    skip_metadata_update: bool = False,
):
    """Update renku existing activities

    Args:
        update_all (bool, optional): Should all activities be updated. Defaults to False.
        paths (Optional[List[PathLike]], optional): Output paths to update the activities for. Defaults to None.
        dry_run (bool, optional): Show what activities would be updated. Defaults to False.
        provider (str, optional):Provider to run the updates. Defaults to "cwltool".
        ignore_deleted (bool, optional): Ignore deleted activities. Defaults to True.
        config (Optional[str], optional): Config file for the provider. Defaults to None.
        skip_metadata_update (bool, optional): Do not update the workflow metadata. Defaults to False.
    """
    try:
        result = (
            update_command(skip_metadata_update=skip_metadata_update)
            .build()
            .execute(
                update_all=update_all,
                dry_run=dry_run,
                paths=paths,
                provider=provider,
                config=config,
                ignore_deleted=ignore_deleted,
            )
        )
    except errors.NothingToExecuteError:
        print(f"Nothing to update/execute for {paths}.")
    else:
        if dry_run:
            activities, modified_inputs = result.output
            print(tabulate_activities(activities, modified_inputs))


def renku_workflow_revert(
    activity_id: str,
    metadata_only: bool = False,
    force: bool = False,
    plan: bool = False,
):
    """Revert an existing activity by id and remove the generated outputs and corresponding plan

    Args:
        activity_id (str): activity id to be removed.
        metadata_only (bool, optional): remove metadata only, but not the generated outputs. Defaults to False.
        force (bool, optional): force, even when activity is part of a composed workflow. Defaults to False.
        plan (bool, optional): remove the corresponding plan that generated the activity as well. Defaults to False.

    Raises:
        errors.ParameterError: If reverting the activity will break downstream workflows
    """
    try:
        revert_activity_command().build().execute(
            metadata_only=metadata_only,
            force=force,
            delete_plan=plan,
            activity_id=activity_id,
        )
    except errors.ActivityDownstreamNotEmptyError:
        raise errors.ParameterError(
            "Activity has downstream dependent activities: Pass '--force' if you want to revert the activity anyways."
        )


def execute_workflow_graph_command(skip_metadata_update: bool): 
    """Wrap execute workflow graph into a renku command for parameter injection

    Args:
        skip_metadata_update (bool): If renku meta data should be updated (if not triples will not be send to the KG)

    Returns:
        Command: Renku command
    """
    command = Command().command(execute_workflow_graph).require_migration()
    if skip_metadata_update:
        command = command.with_database(write=False)
    else:
        command = command.with_database(write=True).with_commit()
    return command


def mod_renku_execute_workflow_graph(dag: DiGraph, provider: str = "toil", config: Optional[str] = None, skip_metadata_update: bool = False):
    """Execute workflow graph 

    Args:
        dag (DiGraph): A graph object with all activities to generate
        provider (str, optional): Workflow runner to use. Defaults to "toil".
        config (Optional[str], optional): Path to config file to specify provider configuration. Defaults to None.
        skip_metadata_update (bool, optional): If renku meta data should be updated (if not triples will not be send to the KG). Defaults to False.
    """
    result = (
        execute_workflow_graph_command(skip_metadata_update=skip_metadata_update)
        .build()
        .execute(
            dag=dag, 
            provider=provider, 
            config=config,
        )
    )