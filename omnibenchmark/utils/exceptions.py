"""Defintions and utils concering exceptions"""

import textwrap


class InterpreterError(Exception):
    @staticmethod
    def format_arg(arg):
        if isinstance(arg, str):
            return arg
        elif isinstance(arg, InterpreterError):
            spec = ""
            if arg.interpreter is not None:
                spec += "Interpreter {}".format(arg.interpreter)
            if arg.extension is not None:
                spec += "Extension {}".format(arg.extension)
            if arg.command is not None:
                spec += "Command {}".format(arg.command)

            if spec:
                spec = " ({})".format(spec)

            return "{}{}:\n{}".format(
                arg.__class__.__name__, spec, textwrap.indent(str(arg), "    ")
            )
        else:
            return "{}: {}".format(arg.__class__.__name__, str(arg))

    def __init__(self, *args, interpreter=None, extension=None, command=None):
        super().__init__("\n".join(self.format_arg(arg) for arg in args))

        self.interpreter = interpreter
        self.extension = extension
        self.command = command


class WorkflowError(Exception):
    pass


class InputError(Exception):
    pass


class OutputError(Exception):
    pass


class ProjectError(Exception):
    pass


class ParameterError(Exception):
    pass
