from omnibenchmark.core.output_classes import OmniOutput
from omnibenchmark.utils.exceptions import OutputError, InputError
import pytest


### Test OmniOutput class
def test_omni_output_with_output_mapping(mock_out_mapping):
    mock_out_mapping["input_files"] = None
    mock_out_mapping["parameter"] = None
    test_output = OmniOutput(
        name="mock_res",
        out_names=["out_file1", "out_file2"],
        file_mapping=[mock_out_mapping],
    )
    assert isinstance(test_output, OmniOutput)


def test_omni_output_with_out_mapping_not_match_names(mock_out_mapping):
    with pytest.raises(InputError, match=r"Expected inputs from .*?"):
        OmniOutput(
            name="mock_res",
            out_names=["quatsch", "out_file2"],
            file_mapping=[mock_out_mapping],
        )


def test_omni_output_without_outmapping_out_end():
    with pytest.raises(
        OutputError, match=r"Undefined outputs. Please specify an output file .*?"
    ):
        OmniOutput(name="mock_res", out_names=["quatsch", "out_file2"])


def test_omni_output_without_mapping_not_match_outend_names():
    with pytest.raises(InputError, match=r"Expected inputs from .*?"):
        OmniOutput(
            name="mock_res",
            out_names=["out_file1", "out_file2"],
            output_end={"out1": ".txt", "out_file2": ".gz"},
        )


def test_omni_output_without_mapping_works():
    test_output = OmniOutput(
        name="mock_res",
        out_names=["out_file1", "out_file2"],
        output_end={"out_file1": ".txt", "out_file2": ".gz"},
    )
    assert isinstance(test_output, OmniOutput)


def test_omni_output_automatic_default(mock_out_mapping):
    mock_out_mapping["input_files"] = None
    mock_out_mapping["parameter"] = None
    test_output = OmniOutput(
        name="mock_res",
        out_names=["out_file1", "out_file2"],
        file_mapping=[mock_out_mapping],
    )
    assert test_output.default == mock_out_mapping["output_files"]


def test_omni_output_default_name_mismatch(mock_out_mapping):
    with pytest.raises(InputError, match=r"Expected inputs from .*?"):
        mis_match = {"out_file1": "path/to/out1", "out_fileX": "path/to/out2"}
        OmniOutput(
            name="mock_res",
            out_names=["out_file1", "out_file2"],
            file_mapping=[mock_out_mapping],
            default=mis_match,
        )
