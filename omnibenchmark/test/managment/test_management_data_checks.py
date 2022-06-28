from omnibenchmark.management import data_checks


### Test renku_dataset_exist
def test_renku_dataset_exist_for_not_existing():
    assert not data_checks.renku_dataset_exist("quatsch")


def test_renku_dataset_exists_for_existing(get_renkuDataset_List):
    assert data_checks.renku_dataset_exist("mock_dataset")


### Test dataset_name_exist
def test_dataset_name_exist_for_not_existing(mock_dataset_query):
    assert not data_checks.dataset_name_exist("quatsch", kg_url="mock_url")


def test_dataset_name_exist_for_existing(mock_dataset_query):
    assert data_checks.dataset_name_exist("mock_dataset", kg_url="mock_url")
