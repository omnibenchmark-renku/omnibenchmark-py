from renku.command.dataset import list_datasets_command
from renku.api import Dataset
import omnibenchmark.management.general_checks


def renku_dataset_list():
    if not omnibenchmark.management.general_checks.is_renku_project():
        return []
    result = list_datasets_command().build().execute()
    data_out = [data._subject for data in result.output]
    data_api = [Dataset._from_dataset(dat) for dat in data_out]
    return data_api
