from omnibenchmark.core.output_classes import OmniCommand, OmniPlan
from omnibenchmark.management import run_commands as omni
import omnibenchmark.renku_commands.workflows as omni_wflow
from omnibenchmark.management import wflow_checks as wflow
from renku.command.command_builder.command import CommandResult
from renku.core.errors import NothingToExecuteError
from omnibenchmark.utils.exceptions import InputError
import pytest


### Test update_activity
@pytest.mark.renku_call
def test_update_activity_no_activity(mock_out_mapping, capsys):
    omni.update_activity(mock_out_mapping)
    captured = capsys.readouterr()
    assert captured.out == r"Nothing to update/execute for*?"


# Test create_activity
def test_create_activity_command(
    mock_out_mapping, mock_plan_dict, mock_plan, monkeypatch
):
    def print_arguments(**kwargs):
        return list(kwargs.values())

    monkeypatch.setattr(omni_wflow, "renku_workflow_execute", print_arguments)
    mock_omni_plan = OmniPlan(plan=mock_plan, param_mapping=mock_plan_dict)
    workflow = omni.create_activity(out_map=mock_out_mapping, omni_plan=mock_omni_plan)

    assert workflow == [
        "XXX",
        [
            "out-1=path/to/out1",
            "out-2=path/to/out2",
            "in-1=path/to/in1",
            "param-1=str_value",
            "param-2=100",
        ],
    ]


def test_create_activity(mock_out_mapping, mock_plan_dict, mock_plan):
    with pytest.raises(NameError, match=r"Could not assign all workflow items from:*?"):
        del mock_plan_dict["in_file1"]
        mock_omni_plan = OmniPlan(plan=mock_plan, param_mapping=mock_plan_dict)
        omni.create_activity(out_map=mock_out_mapping, omni_plan=mock_omni_plan)


# Test manage_renku_plan
def test_manage_renku_plan_with_correct_plan(mock_plan, mock_plan_view, monkeypatch):
    def return_mock_plan(*args, **kwargs):
        return mock_plan

    monkeypatch.setattr(wflow, "check_plan_exist", return_mock_plan)
    mock_omni_plan = OmniPlan(plan=mock_plan_view)
    out_plan = omni.manage_renku_plan(
        out_files=["any", "random"],
        omni_plan=mock_omni_plan,
        command="not_to_run_command_str",
    )
    assert out_plan.plan.id == mock_omni_plan.plan.id


def test_manage_renku_plan_without_any_input(mock_plan_view, monkeypatch):
    def return_run_result(*args, **kwargs):
        return CommandResult(output=mock_plan_view, error=None, status=None)

    monkeypatch.setattr(omni_wflow, "renku_workflow_run", return_run_result)
    mock_omni_plan = OmniPlan(plan=mock_plan_view, param_mapping={})
    out_plan = omni.manage_renku_plan(
        out_files=["any", "random"], omni_plan=None, command="not_to_run_command_str"
    )
    assert out_plan.param_mapping == mock_omni_plan.param_mapping
    assert out_plan.plan == mock_omni_plan.plan


# Test check_omni_command
def test_check_omni_command_with_command():
    mock_command = OmniCommand(
        script="path/to/no/script", command_line="no real command"
    )
    assert (
        omni.check_omni_command(command=mock_command, script=None, outputs=None)
        == mock_command
    )


def test_check_omni_command_no_command_script():
    with pytest.raises(InputError, match=r"Can not run a command*?"):
        assert omni.check_omni_command(command=None, script=None, outputs=None)


# Test get_all_output_file_names
def test_get_all_output_file_names_with_output(mock_omni_output):
    assert omni.get_all_output_file_names(mock_omni_output) == [
        "path/to/out1",
        "path/to/out2",
    ]


def test_get_all_output_file_names_with_no_outfiles(mock_omni_output):
    mock_omni_output.file_mapping = {}
    assert omni.get_all_output_file_names(mock_omni_output) == []


# Test manage_renku_activities
# def test_manage_renku_activities_new_and_existing_activities(mock_omni_output, mock_out_mapping, monkeypatch):
#
#    def return_outfile_list(*args,**kwargs):
#        return ["path/to/out1"]
#
#    monkeypatch.setattr(
#        wflow,
#        "filter_activity_exist",
#        return_outfile_list,
#    )
#    mock_out_mapping2 = mock_out_mapping
#    mock_out_mapping2["output_files"] = {"out_file1": "path/to/out3", "out_file2": "path/to/out4"}
#    mock_omni_output.file_mapping.append(mock_out_mapping)
#
#    def return_arguments(*args, **kwargs):
#        return kwargs.values()
#
#    monkeypatch.setattr(
#        "omnibenchmark.management.run_commands.create_activity",
#        return_arguments,
#    )
#
#    monkeypatch.setattr(
#        "omnibenchmark.management.run_commands.update_activity",
#        return_arguments,
#    )
#    assert omni.manage_renku_activities(mock_omni_output, omni_plan=None) == [mock_out_mapping, mock_out_mapping2]
