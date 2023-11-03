from __future__ import annotations
import logging
from typing import Any, TypeVar, Optional, List, Union, Dict
from pathlib import Path
from renku.domain_model.dataset import Dataset as RenkuDataSet
import omnibenchmark.management.general_checks
from omnibenchmark.utils.default_global_vars import DATA_QUERY_URL
from omnibenchmark.management.data_checks import dataset_slug_exist, renku_dataset_exist
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
    slug: str,
    data_query_url: str = DATA_QUERY_URL,
    name: Optional[str] = None,
    description: Optional[str] = None,
    creators: Optional[List[str]] = None,
    meta_data: Optional[Dict[str, Any]] = None,
    keyword: Optional[List[str]] = None,
    storage: Optional[str] = None,
    datadir: Optional[str] = None,
    check_slug: bool = True,
) -> RenkuDataSet:
    """Generate an empty renku dataset in the current project. Works in a renku project only.

    Args:
        slug ([str]): Dataset name
        name (str, optional): Dataset name. Defaults to None.
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

    if renku_dataset_exist(slug):
        print(f"Dataset {slug} already exists in this repository.")
        return

    if check_slug and dataset_slug_exist(slug=slug, data_query_url= data_query_url):
        print(f"Dataset {slug} already taken. Please use a different slug.")
        return

    result = (
        create_dataset_command()
        .build()
        .execute(
            slug=slug,
            name=name,
            description=description,
            creators=creators,
            keywords=keyword,
            custom_metadata=meta_data,
            storage=storage,
            datadir=datadir,
        )
    )
    print(
        f"Renku dataset with name {slug} and the following keywords {keyword} was generated."
    )
    return result.output


def renku_dataset_import(
    uri: str, slug: Optional[str] = None, extract: bool = False, yes: bool = True, datadir: Optional[str] = None, 
    previous_dataset: Optional[str] = None,
    delete: bool = False,
    gitlab_token: Optional[str] = None,**kwargs
):
    """Import renku dataset by url

    Args:
        uri (str): URL to the dataset to import
        slug(str, optional): Slug of the imported dataset. Defaults to None.
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

    if slug is not None:
        if renku_dataset_exist(slug):
            logger.info(f"Dataset {slug} already exists in this repository.")
            return

    result = (
        import_dataset_command()
        .build()
        .execute(uri=uri, slug=slug, extract=extract, yes=yes, datadir=datadir, previous_dataset=previous_dataset, delete=delete, gitlab_token=gitlab_token, **kwargs)
    )

    return result.output


def renku_dataset_update(
    slugs: List[str],
    creators: Optional[List[str]] = None,
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    ref: Optional[str] = None,
    delete: bool = True,
    no_local: bool = False,
    no_remote: bool = False,
    check_data_directory: bool = False,
    update_all: bool = False,
    dry_run: bool = False,
    plain: bool = False,
):
    """Update an imported renku dataset from source

    Args:
        slugs (List[str]): Slugs of the dataset
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
        and len(slugs) == 0
        and include is None
        and exclude is None
        and not dry_run
    ):
        raise errors.ParameterError(
            "Either names, update_all, dry_run, or include/exclude should be specified"
        )

    if len(slugs) >= 1 and update_all:
        raise errors.ParameterError("Cannot pass dataset names with update_all")
    elif (include or exclude is not None) and update_all:
        raise errors.ParameterError("Cannot pass include/exclude with update_all")

    result = (
        update_datasets_command(dry_run=dry_run)
        .build()
        .execute(
            slugs=slugs,
            creators=creators,
            include=include,
            exclude=exclude,
            ref=ref,
            delete=delete,
            update_all=update_all,
            dry_run=dry_run,
            no_local=no_local,
            no_remote=no_remote,
            check_data_directory=check_data_directory,
            plain=plain,
        )
    )

    return result.output


def renku_add_to_dataset(
    urls: List[str],
    dataset_slug: str,
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
        dataset_slug (str): Slug of the dataset
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
        datadir = "data/" + dataset_slug

    result = (
        add_to_dataset_command()
        .build()
        .execute(
            urls=urls,
            dataset_slug=dataset_slug,
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
    slug: str,
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    yes: bool = True,
):
    """Unlink files from renku dataset

    Args:
        slug (str): Dataset name to unlink files from.
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
        slug=slug, include=include, exclude=exclude, yes=yes
    )


def renku_dataset_remove(slug: str):
    """Remove renku dataset from the current project

    Args:
        slug (str): Slug of the dataset to remove from the project

    Raises:
        ProjectError: raised if the project is not a renku project.
    """
    if not omnibenchmark.management.general_checks.is_renku_project():
        raise ProjectError(
            "Directory is not a renku project.\n"
            "Make sure you are in the correct context.\n"
            "No files were added."
        )

    remove_dataset_command().build().execute(slug)
