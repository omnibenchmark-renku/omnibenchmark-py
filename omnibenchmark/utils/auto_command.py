"""Utils functions to facilitate automatization from/for inputs"""

from omnibenchmark.utils.exceptions import InterpreterError
from typing import Mapping, Union, List, Any, Optional
import os.path
from os import PathLike


def get_interpreter_from_extension(ext: str) -> str:
    """Automatically gets the interpreter to run a script with from the scripts file extension.

    Args:
        ext (str): File extension from the script, that should be run as workflow

    Raises:
        InterpreterError: Error, if no known interpreter can be identified.

    Returns:
        str: Interpreter type, e.g. R, python, bash, julia
    """

    interpreter = {"r": "R", "py": "python", "sh": "bash", "jl": "julia"}.get(
        ext.lstrip(".").lower(), None
    )

    if interpreter is None:
        raise InterpreterError(
            "Interpreter could not be identified from extention {}. Please specify command explicitly.".format(
                ext
            )
        )
    else:
        return interpreter


def get_command_start_from_interpreter(interpreter: str) -> str:
    """Automatically generates the command start to run a script with from the interpreter name.

    Args:
        interpreter (str): Interpreter to run a script with, e.g., R, python

    Raises:
        InterpreterError: Error, if no known interpreter can be identified.

    Returns:
        str: Command start to run the script with
    """

    command_start = {
        "r": "Rscript --vanilla",
        "python": "python",
        "bash": "bash",
        "julia": "julia",
    }.get(interpreter.lower(), None)

    if command_start is None:
        raise InterpreterError(
            "Command start could not be identified from interpreter {}. Please specify interpreter and command explicitly.".format(
                interpreter
            )
        )
    else:
        return command_start


def parse_command_line_args(arg_map: Mapping[str, str]) -> List[str]:
    return [
        '--{} "{}"'.format(str(arg_nam), arg_val)
        for arg_nam, arg_val in arg_map.items()
    ]


def automatic_command_generation(
    script: Union[PathLike, str],
    interpreter: str = None,
    inputs: Optional[Mapping[str, str]] = None,
    parameters: Optional[Mapping[str, str]] = None,
    outputs: Optional[Mapping[str, str]] = None,
) -> str:
    """Automatic generate a command line command to run with renku run

    Args:
        script (PathLike): Path to script to run
        interpreter (str, optional): Interpreter to use to run the script. Defaults to None.
        inputs (Mapping, optional): Default inputs to run the script. Defaults to None.
        parameters (Mapping, optional): Default parameter to run the script with. Defaults to None.
        outputs (Mapping, optional): Default outputs generated. Defaults to None.

    Returns:
        str: A command line command to run the script with and parse all inputs/parameter/output names as commandline options (format --name value)
    """
    if interpreter is None:
        ext = os.path.splitext(script)[1]
        interpreter = get_interpreter_from_extension(ext)

    command_start = get_command_start_from_interpreter(interpreter)

    arg_list: List[str] = []
    arg_list.extend(
        parse_command_line_args(arg_map)  # type: ignore
        for arg_map in [inputs, outputs, parameters]
        if not arg_map is None
    )
    flat_list = [item for sublist in arg_list for item in sublist]
    command_list = [command_start, script]
    command_list.extend(flat_list)
    command_line = " ".join(command_list)  # type:ignore
    return command_line
