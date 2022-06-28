""" All test around the OmniParameter class and related functions"""

from omnibenchmark.core.input_classes import OmniParameter
from omnibenchmark.utils.exceptions import InputError
import pytest

### Test OmniParameter class


def test_omni_parameter_with_values(mock_param_values):
    omni_p = OmniParameter(names=["param1", "param2"], values=mock_param_values)
    assert isinstance(omni_p, OmniParameter)


def test_omni_parameter_default(mock_param_values):
    omni_p = OmniParameter(names=["param1", "param2"], values=mock_param_values)
    assert omni_p.default == {"param1": 0, "param2": "test"}


def test_omni_parameter_value_names(mock_param_values):
    with pytest.raises(InputError, match=r"Expected inputs from .*?"):
        OmniParameter(names=["no_param", "param2"], values=mock_param_values)


def test_omni_parameter_comb_names(mock_combinations):
    with pytest.raises(InputError, match=r"Expected inputs from .*?"):
        OmniParameter(names=["no_param", "param2"], combinations=mock_combinations)
