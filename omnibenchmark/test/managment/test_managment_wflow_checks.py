from omnibenchmark.management import wflow_checks
from renku.infrastructure.gateway.activity_gateway import ActivityGateway
from omnibenchmark.management import general_checks
import pytest

### Test activity_plan_is_valid
def test_activity_plan_is_valid_no_activity(act_gateway):

    assert isinstance(
        wflow_checks.activity_plan_is_valid(output="", activity_gateway=act_gateway),
        type(None),
    )


def test_activity_plan_is_valid_invalid_activity(
    mock_activity, monkeypatch, act_gateway
):

    mock_activity.association.plan.invalidated_at = "today"

    def get_mock_activity():
        return [mock_activity]

    monkeypatch.setattr(
        ActivityGateway,
        "get_activities_by_generation",
        lambda *args, **kwargs: get_mock_activity(),
    )

    assert isinstance(
        wflow_checks.activity_plan_is_valid(".", activity_gateway=act_gateway),
        type(None),
    )


def test_activity_plan_is_valid_valid_activity(mock_activity, monkeypatch, act_gateway):
    def get_mock_activity():
        return [mock_activity]

    def get_mock_status():
        return True

    monkeypatch.setattr(
        ActivityGateway,
        "get_activities_by_generation",
        lambda *args, **kwargs: get_mock_activity(),
    )
    monkeypatch.setattr(
        general_checks, "is_renku_project", lambda *args, **kwargs: get_mock_status()
    )

    assert (
        wflow_checks.activity_plan_is_valid("test_output", activity_gateway=act_gateway)
        == "test_output"
    )


### Test filter_activity_exist
def test_filter_activity_exist_gateway_establishment(mock_activity, monkeypatch):
    def get_mock_activity():
        return [mock_activity]

    monkeypatch.setattr(
        ActivityGateway,
        "get_activities_by_generation",
        lambda *args, **kwargs: get_mock_activity(),
    )

    def get_mock_status():
        return True

    monkeypatch.setattr(
        general_checks, "is_renku_project", lambda *args, **kwargs: get_mock_status()
    )

    assert wflow_checks.filter_activity_exist(["test_output1", "test_output2"]) == [
        "test_output1",
        "test_output2",
    ]


# Test get_all_plans
def test_get_all_plans_no_plans():
    assert wflow_checks.get_all_plans() == []


# Test filter_valid_plans
def test_filter_valid_plans_no_plans():
    assert wflow_checks.filter_valid_plans([]) == []


def test_filter_valid_plans_valid(mock_plan):
    assert wflow_checks.filter_valid_plans([mock_plan]) == [mock_plan]


def test_filter_valid_plans_valid_invalid(mock_plan):
    mock_plan.invalidated_at = "today"
    assert wflow_checks.filter_valid_plans([mock_plan]) == []


# Test get_plan_output_values
def test_get_plan_output_values_no_outputs(mock_plan):
    assert wflow_checks.get_plan_output_values(mock_plan) == []


def test_get_plan_output_values_detect_output(mock_plan, mock_output):
    mock_output.default_value = "path/to/default/output.test"
    mock_plan.outputs = [mock_output]
    assert wflow_checks.get_plan_output_values(mock_plan) == [
        "path/to/default/output.test"
    ]


# Test get_plan_id_from_output
def test_get_plan_id_from_output_without_plan(act_gateway):

    assert (
        wflow_checks.get_plan_id_from_output(
            "test_output", activity_gateway=act_gateway
        )
        == []
    )


def test_get_plan_id_from_output_with_plan(mock_activity, monkeypatch, act_gateway):
    def get_mock_activity():
        return [mock_activity]

    monkeypatch.setattr(
        ActivityGateway,
        "get_activities_by_generation",
        lambda *args, **kwargs: get_mock_activity(),
    )

    def get_mock_status():
        return True

    monkeypatch.setattr(
        general_checks, "is_renku_project", lambda *args, **kwargs: get_mock_status()
    )

    assert wflow_checks.get_plan_id_from_output(
        "test_output", activity_gateway=act_gateway
    ) == ["XXX"]


# Test find_plan_by_outputs
def test_find_plan_by_outputs_no_plan():
    assert wflow_checks.find_plan_by_outputs(["test_output"]) == []


def test_find_plan_by_outputs_with_plan(monkeypatch, mock_plan):
    def get_mock_plan():
        return [mock_plan]

    def mock_plan_id():
        return ["XXX"]

    monkeypatch.setattr(
        wflow_checks, "filter_valid_plans", lambda *args, **kwargs: get_mock_plan()
    )

    monkeypatch.setattr(
        wflow_checks, "get_plan_id_from_output", lambda *args, **kwargs: mock_plan_id()
    )

    assert wflow_checks.find_plan_by_outputs(["test_output"]) == [mock_plan]


# Test check_plan_exist
def test_check_plan_exist_no_plan():
    assert wflow_checks.check_plan_exist(["test_output1", "test/output2"]) == None


def test_check_plan_exist_one_plan(mock_plan, monkeypatch):
    def get_mock_plan():
        return [mock_plan]

    monkeypatch.setattr(
        wflow_checks, "find_plan_by_outputs", lambda *args, **kwargs: get_mock_plan()
    )

    assert wflow_checks.check_plan_exist(["test_output1", "test/output2"]) == mock_plan


def test_check_plan_exist_two_plans(mock_plan, monkeypatch):
    def get_mock_plan():
        return [mock_plan, mock_plan]

    monkeypatch.setattr(
        wflow_checks, "find_plan_by_outputs", lambda *args, **kwargs: get_mock_plan()
    )
    with pytest.raises(Exception) as e_info:
        wflow_checks.check_plan_exist(["test_output1", "test/output2"])
