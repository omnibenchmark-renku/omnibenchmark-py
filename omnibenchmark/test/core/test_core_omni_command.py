""" Tests related to the command class"""

from omnibenchmark.core.output_classes import OmniCommand

# Test OmniCommand class
def test_omni_command_with_command_line():
    test_command = OmniCommand(
        script="path/to/some/sricpt.jl",
        command_line='julia path/to/some/script.jl --input "in1"',
    )
    assert isinstance(test_command, OmniCommand)


def test_omni_command_with_output_command_line(mock_omni_output):
    test_command = OmniCommand(
        script="path/to/some/sricpt.jl",
        outputs=mock_omni_output,
        command_line='julia path/to/some/script.jl --input "in1"',
    )
    assert test_command.command_line == 'julia path/to/some/script.jl --input "in1"'


def test_omni_command_with_output(mock_omni_output):
    test_command = OmniCommand(
        script="path/to/some/sricpt.jl", outputs=mock_omni_output
    )
    assert (
        test_command.command_line
        == 'julia path/to/some/sricpt.jl --dim_red_file "path/to/dim/red" --count_file "path/to/count" --out_file1 "path/to/out1" --out_file2 "path/to/out2" --param1 "0" --param2 "test"'
    )
