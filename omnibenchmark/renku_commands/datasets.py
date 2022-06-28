from __future__ import annotations
import logging
from typing import Any, TypeVar, Optional, List, Union, Dict
from pathlib import Path
from renku.command.dataset import create_dataset_command
from renku.domain_model.dataset import Dataset as RenkuDataSet
import omnibenchmark.management.general_checks
from omnibenchmark.management.data_checks import dataset_name_exist, renku_dataset_exist
from renku.command.dataset import (
    import_dataset_command,
    update_datasets_command,
    add_to_dataset_command,
)
from renku.core import errors
from omnibenchmark.utils.exceptions import ProjectError

PathLike = TypeVar("PathLike", str, Path, None)
logger = logging.getLogger("omnibenchmark.renku_commands")


def renku_dataset_create(
    name: str,
    kg_url: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    creators: Optional[List[str]] = None,
    meta_data: Optional[Dict[str, Any]] = None,
    keyword: Optional[List[str]] = None,
) -> RenkuDataSet:
    """Generate an empty renku dataset in the current project. Works in a renku project only.

    Args:
        name ([str]): Dataset name
        title (str, optional): Dataset title. Defaults to None.
        description (str, optional): Description of the dataset. Defaults to None.
        creators (str, optional): Dataset creator. Defaults to None, which will be the github account activated for that renku project.
        metadata (PathLike, optional): Path to json or yaml file containing meta data information. Defaults to None.
        keyword (list[str], optional): List of keywords to be associated with the dataset. Defaults to None.

    Returns:
        RenkuDataSet: An object of class Dataset from renku.core.models.dataset
    """
    if not omnibenchmark.management.general_checks.is_renku_project():
        raise ProjectError(
            "Directory is not a renku project.\n"
            "Make sure you are in the correct context.\n"
            "No dataset was created."
        )

    if renku_dataset_exist(name):
        print(f"Dataset {name} already exists in this repository.")
        return

    if dataset_name_exist(name, kg_url):
        print(f"Dataset {name} already taken. Please use a different name.")
        return

    result = (
        create_dataset_command()
        .build()
        .execute(
            name=name,
            title=title,
            description=description,
            creators=creators,
            keywords=keyword,
            custom_metadata=meta_data,
        )
    )
    print(
        f"Renku dataset with name {name} and the following keywords {keyword} was generated."
    )
    return result.output


def renku_dataset_import(
    uri: str, name: str = None, extract: bool = False, yes: bool = True
):
    if not omnibenchmark.management.general_checks.is_renku_project():
        raise ProjectError(
            "Directory is not a renku project.\n"
            "Make sure you are in the correct context.\n"
            "No dataset was imported."
        )

    if name is not None:
        if renku_dataset_exist(name):
            logger.info(f"Dataset {name} already exists in this repository.")
            return

    result = (
        import_dataset_command()
        .build()
        .execute(uri=uri, name=name, extract=extract, yes=yes)
    )

    return result.output


def renku_dataset_update(
    names: List[str],
    creators: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    ref: Optional[str] = None,
    delete: bool = True,
    no_external: bool = True,
    update_all: bool = False,
    dry_run: bool = False,
):
    if not omnibenchmark.management.general_checks.is_renku_project():
        raise ProjectError(
            "Directory is not a renku project.\n"
            "Make sure you are in the correct context.\n"
            "No dataset was updated."
        )

    if (
        not update_all
        and len(names) == 0
        and include is None
        and exclude is None
        and not dry_run
    ):
        raise errors.ParameterError(
            "Either names, update_all, dry_run, or include/exclude should be specified"
        )

    if len(names) >= 1 and update_all:
        raise errors.ParameterError("Cannot pass dataset names with update_all")
    elif (include or exclude is not None) and update_all:
        raise errors.ParameterError("Cannot pass include/exclude with update_all")

    result = (
        update_datasets_command()
        .build()
        .execute(
            names=names,
            creators=creators,
            include=include,
            exclude=exclude,
            ref=ref,
            delete=delete,
            no_external=no_external,
            update_all=update_all,
            dry_run=dry_run,
        )
    )

    return result.output


def renku_add_to_dataset(
    urls: List[str],
    dataset_name: str,
    external: bool = False,
    force: bool = False,
    overwrite: bool = True,
    create: bool = False,
    sources: Optional[List[Union[str, Path]]] = None,
    destination: Optional[List[str]] = None,
    ref: Optional[str] = None,
) -> Optional[RenkuDataSet]:

    if not omnibenchmark.management.general_checks.is_renku_project():
        raise ProjectError(
            "Directory is not a renku project.\n"
            "Make sure you are in the correct context.\n"
            "No files were added."
        )

    result = (
        add_to_dataset_command()
        .build()
        .execute(
            urls=urls,
            dataset_name=dataset_name,
            external=external,
            force=force,
            overwrite=overwrite,
            create=create,
            sources=sources,
            destination=destination,
            ref=ref,
        )
    )
    return result
