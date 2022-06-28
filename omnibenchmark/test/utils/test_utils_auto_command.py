""" Test around automatic command generation"""

import omnibenchmark.utils.auto_command as omni
from omnibenchmark.utils.exceptions import InterpreterError
import pytest

### Test get_interpreter_from_extension
def test_get_interpreter_from_extension_existing():
    assert omni.get_interpreter_from_extension("sh") == "bash"


def test_get_interpreter_from_extension_lower():
    assert omni.get_interpreter_from_extension("Py") == "python"


def test_get_interpreter_from_extension_remove_dot():
    assert omni.get_interpreter_from_extension(".R") == "R"


def test_get_interpreter_from_extension_unknown():
    with pytest.raises(
        InterpreterError,
        match=r"Interpreter could not be identified from extention xy.*?",
    ):
        omni.get_interpreter_from_extension("xy")


### Test get_command_start_from_interpreter
def test_get_command_start_from_interpreter_existing():
    assert omni.get_command_start_from_interpreter("R") == "Rscript --vanilla"


def test_get_command_start_from_interpreter_unknown():
    with pytest.raises(
        InterpreterError,
        match=r"Command start could not be identified from interpreter fancy.*?",
    ):
        omni.get_command_start_from_interpreter("fancy")


### Test parse_command_line_args
def test_parse_command_line_args_existing():
    assert omni.parse_command_line_args({"input1": "in1", "input2": "in2"}) == [
        '--input1 "in1"',
        '--input2 "in2"',
    ]


### Test automatic_command_generation
def test_automatic_command_generation_with_interpretor():
    command = omni.automatic_command_generation(
        script="path/to/script.py",
        interpreter="python",
        inputs={"input1": "in1", "input2": "in2"},
    )
    assert command == 'python path/to/script.py --input1 "in1" --input2 "in2"'


def test_automatic_command_generation_no_interpretor():
    command = omni.automatic_command_generation(
        script="path/to/script.py", inputs={"input1": "in1", "input2": "in2"}
    )
    assert command == 'python path/to/script.py --input1 "in1" --input2 "in2"'


def test_automatic_command_generation_all():
    command = omni.automatic_command_generation(
        script="path/to/script.py",
        inputs={"input1": "in1", "input2": "in2"},
        parameters={"param1": "p1"},
        outputs={"output1": "out1"},
    )
    assert (
        command
        == 'python path/to/script.py --input1 "in1" --input2 "in2" --output1 "out1" --param1 "p1"'
    )


def test_automatic_command_generation_none():
    command = omni.automatic_command_generation(script="path/to/script.py")
    assert command == "python path/to/script.py"
