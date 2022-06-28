""" All test around the OmniInput class and related functions"""

from omnibenchmark.core.input_classes import OmniInput
from omnibenchmark.utils.exceptions import InputError
import pytest


### Test OmniInput class
def test_omni_input_with_input_files(mock_inputfiles):
    test_input = OmniInput(
        names=["dim_red_file", "count_file"], input_files=mock_inputfiles
    )
    assert isinstance(test_input, OmniInput)


def test_omni_input_with_input_files_not_match_names(mock_inputfiles):
    with pytest.raises(InputError, match=r"Expected inputs from .*?"):
        OmniInput(names=["no_name", "count_file"], input_files=mock_inputfiles)


def test_omni_input_no_input_files_no_prefix():
    with pytest.raises(InputError, match=r"Missing input file definition"):
        OmniInput(names=["dim_red_file", "count_file"])


def test_omni_input_no_input_files_with_prefix_not_match_names():
    with pytest.raises(InputError, match=r"Expected inputs from .*?"):
        OmniInput(
            names=["dim_red_file", "count_file"],
            prefix={"dim_red_file": ["some"], "no_name": ["another"]},
            keyword=["some"],
        )


def test_omni_input_no_default(mock_inputfiles):
    test_input = OmniInput(
        names=["dim_red_file", "count_file"], input_files=mock_inputfiles
    )
    assert test_input.default == "data1"


def test_omni_input_no_default_files(mock_inputfiles):
    test_input = OmniInput(
        names=["dim_red_file", "count_file"], input_files=mock_inputfiles
    )
    assert test_input.default_files == mock_inputfiles["data1"]


def test_omni_input_default_name_mismatch(mock_inputfiles):
    with pytest.raises(InputError, match=r"Input default data3 not found.*?"):
        OmniInput(
            names=["dim_red_file", "count_file"],
            input_files=mock_inputfiles,
            default="data3",
        )


# def test_omni_input_get_input_files(mock_inputfiles, monkeypatch):
#    def get_mock_infiles():
#        return mock_inputfiles
#
#
#    monkeypatch.setattr(
#        omnibenchmark.utils.auto_input,
#        "get_input_files_from_prefix",
#        lambda *args, **kwargs: get_mock_infiles(),
#    )
#
#    test_input = OmniInput(names=["dim_red_file", "count_file"], prefix={"dim_red_file": ["some"], "count_file": ["another"]})
#
#    assert isinstance(test_input, OmniInput)
