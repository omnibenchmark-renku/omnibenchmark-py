from __future__ import annotations
import logging
from typing import Any, TypeVar, Optional, List, Union, Dict
from pathlib import Path
from renku.domain_model.dataset import Dataset as RenkuDataSet
import omnibenchmark.management.general_checks
from omnibenchmark.management.data_checks import dataset_name_exist, renku_dataset_exist
from renku.command.dataset import (
    create_dataset_command,
    import_dataset_command,
    update_datasets_command,
    add_to_dataset_command,
    file_unlink_command,
    remove_dataset_command,
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
    storage: Optional[str] = None,
    datadir: Optional[str] = None
) -> RenkuDataSet:
    """Generate an empty renku dataset in the current project. Works in a renku project only.

    Args:
        name ([str]): Dataset name
        title (str, optional): Dataset title. Defaults to None.
        description (str, optional): Description of the dataset. Defaults to None.
        creators (str, optional): Dataset creator. Defaults to None,
                                  which will be the github account activated for that renku project.
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
            storage=storage,
            datadir=datadir,
        )
    )
    print(
        f"Renku dataset with name {name} and the following keywords {keyword} was generated."
    )
    return result.output


def renku_dataset_import(
    uri: str, name: Optional[str] = None, extract: bool = False, yes: bool = True, datadir: Optional[str] = None, **kwargs
):
    """Import renku dataset by url

    Args:
        uri (str): URL to the dataset to import
        name (str, optional): Name of the imported dataset. Defaults to None.
        extract (bool, optional): If the dataset is zipped and shall be extracted. Defaults to False.
        yes (bool, optional): Skip manual confirmation. Defaults to True.

    Raises:
        ProjectError: Project to import the dataset into needs to be a renku project
    """
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
        .execute(uri=uri, name=name, extract=extract, yes=yes, datadir=datadir, **kwargs)
    )

    return result.output


def renku_dataset_update(
    names: List[str],
    creators: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    ref: Optional[str] = None,
    delete: bool = True,
    no_local: bool = False,
    no_remote: bool = False,
    no_external: bool = False,
    check_data_directory: bool = False,
    update_all: bool = False,
    dry_run: bool = False,
    plain: bool = False,
):
    """Update an imported renku dataset from source

    Args:
        names (List[str]):name of the dataset
        creators (Optional[List[str]], optional): Original dataset creator. Defaults to None.
        include (Optional[List[str]], optional): Files to include into the update. Defaults to None.
        exclude (Optional[List[str]], optional): Files to exclude from updating. Defaults to None.
        ref (Optional[str], optional): commit hash to update the dataset from. Defaults to None.
        delete (bool, optional): Delete files that do not exist in source. Defaults to True.
        update_all (bool, optional): Update all dataset files. Defaults to False.
        dry_run (bool, optional): Dry run the update. Defaults to False.

    Raises:
        ProjectError: The project needs to be a renku project
        errors.ParameterError: Specify only one of exclude/include and update_all
    """
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
        update_datasets_command(dry_run=dry_run)
        .build()
        .execute(
            names=names,
            creators=creators,
            include=include,
            exclude=exclude,
            ref=ref,
            delete=delete,
            update_all=update_all,
            dry_run=dry_run,
            no_local=no_local,
            no_remote=no_remote,
            no_external=no_external,
            check_data_directory=check_data_directory,
            plain=plain,
        )
    )

    return result.output


def renku_add_to_dataset(
    urls: List[str],
    dataset_name: str,
    force: bool = False,
    overwrite: bool = True,
    create: bool = False,
    datadir: Optional[Union[str, Path]] = None,
    destination: Optional[List[str]] = None,
    **kwargs,
) -> Optional[RenkuDataSet]:
    """Add files to renku dataset

    Args:
        urls (List[str]): Urls to add
        dataset_name (str): Name of the dataset
        external (bool, optional): Do urls point to external files. Defaults to False.
        force (bool, optional): Force overwriting of files. Defaults to False.
        overwrite (bool, optional): Ovrwrite files. Defaults to True.
        create (bool, optional): Create the dataset if it does not exist already. Defaults to False.
        sources (Optional[List[Union[str, Path]]], optional): Sources to add files from. Defaults to None.
        destination (Optional[List[str]], optional): Destinations of the added files. Defaults to None.

    Raises:
        ProjectError: The project needs to be a renku project
    """

    if not omnibenchmark.management.general_checks.is_renku_project():
        raise ProjectError(
            "Directory is not a renku project.\n"
            "Make sure you are in the correct context.\n"
            "No files were added."
        )

    if datadir is None:
        datadir = "data/" + dataset_name

    result = (
        add_to_dataset_command()
        .build()
        .execute(
            urls=urls,
            dataset_name=dataset_name,
            force=force,
            overwrite=overwrite,
            create=create,
            destination=destination,
            datadir=datadir,
            **kwargs,
        )
    )
    return result


def renku_unlink_from_dataset(
    name: str,
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    yes: bool = True,
):
    """Unlink files from renku dataset

    Args:
        name (str): Dataset name to unlink files from.
        include (Optional[str], optional): Pattern of files to include. Defaults to None.
        exclude (Optional[str], optional): Pattern of files to exclude. Defaults to None.
        yes (bool, optional): confirm file unlinking. Defaults to True.

    Raises:
        ProjectError: Project needs to be a renku project to perform renku actions.
        errors.ParameterError: At least one of include or exclude need to be defined.
    """

    if not omnibenchmark.management.general_checks.is_renku_project():
        raise ProjectError(
            "Directory is not a renku project.\n"
            "Make sure you are in the correct context.\n"
            "No files were added."
        )
    if not include and not exclude:
        raise errors.ParameterError(
            (
                "Include or exclude filters not found.\n"
                "Please specify at least one of include and/or exclude'\n"
            )
        )

    file_unlink_command().build().execute(
        name=name, include=include, exclude=exclude, yes=yes
    )


def renku_dataset_remove(data_name: str):
    """Remove renku dataset from the current project

    Args:
        data_name (str): Name of the dataset to remove from the project

    Raises:
        ProjectError: raised if the project is not a renku project.
    """
    if not omnibenchmark.management.general_checks.is_renku_project():
        raise ProjectError(
            "Directory is not a renku project.\n"
            "Make sure you are in the correct context.\n"
            "No files were added."
        )

    remove_dataset_command().build().execute(data_name)
