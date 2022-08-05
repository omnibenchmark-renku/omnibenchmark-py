"""Renku workflow commands"""

from __future__ import annotations
from typing import List, Optional, Mapping, Union
from omnibenchmark.core.input_classes import PathLike
from renku.command.run import run_command
from renku.command.workflow import execute_workflow_command
from renku.command.update import update_command
from renku.command.command_builder.command import CommandResult
from renku.core import errors
from renku.command.format.activity import tabulate_activities
from omnibenchmark.management.general_checks import is_renku_project
import logging

logger = logging.getLogger("omnibenchmark.renku_commands")


def renku_workflow_run(
    command_line: str,
    name: str = None,
    description: str = None,
    keyword: str = None,
    success_codes: List[int] = None,
    explicit_inputs: List = [],
    explicit_outputs: List = [],
    explicit_parameters: List = [],
    no_output: bool = False,
    no_input_detection: bool = False,
    no_output_detection: bool = False,
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
            f"Project is not a renku project. No workflow generated, consider to running your command without renku."
        )
        return

    workflow = (
        run_command()
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
        )
    )

    return workflow


def renku_workflow_execute(
    name_or_id: str,
    set_params: List[str],
    provider: str = "cwltool",
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
    provider: str = "cwltool",
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
