import logging
import sys, os, functools


def get_logger(log_file_name, log_level=logging.INFO, log_sub_dir=""):
    """Creates a Log File and returns Logger object

    Args:
        log_level:     The log level.
        log_file_name: The log file name.
        log_sub_dir:   The directory to save log files to.
    """

    # Build Log File Full Path
    logPath = (
        log_file_name
        if os.path.exists(log_file_name)
        else os.path.join(log_sub_dir, (str(log_file_name) + ".log"))
    )

    # Create logger object and set the format for logging and other attributes
    logger = logging.Logger(log_file_name)

    # create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # create file handler
    handler = logging.FileHandler(logPath, "a+")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Set loglevel
    logger.setLevel(log_level)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # add ch to logger
    logger.addHandler(ch)

    # Return logger object
    return logger


def log_decorator(_func=None):
    def log_decorator_info(func):
        @functools.wraps(func)
        def log_decorator_wrapper(self, *args, **kwargs):
            """Build logger object"""
            logger_obj = get_logger(
                log_file_name=self.log_file_name,
                log_level=self.log_level,
                log_sub_dir=self.log_file_dir,
            )

            """ Create a list of the positional arguments passed to function."""
            args_passed_in_function = [repr(a) for a in args]

            """ Create a list of the keyword arguments."""
            kwargs_passed_in_function = [f"{k}={v!r}" for k, v in kwargs.items()]

            """ The lists of positional and keyword arguments is joined together to form final string """
            formatted_arguments = ", ".join(
                args_passed_in_function + kwargs_passed_in_function
            )

            """log function begining"""
            logger_obj.info(f"Arguments: {formatted_arguments} - Begin function")
            try:
                """log return value from the function"""
                value = func(self, *args, **kwargs)
                logger_obj.info(f"Returned: - End function {value!r}")
            except:
                """log exception if occurs in function"""
                logger_obj.error(f"Exception: {str(sys.exc_info()[1])}")
                raise
            return value

        return log_decorator_wrapper

    if _func is None:
        return log_decorator_info
    else:
        return log_decorator_info(_func)


import logging


def create_logger(log_level):
    """General logger for OmniBench class

    Args:
        log_level ([type]): The log level.
    """
    logger = logging.getLogger("OmniBench")
    logger.setLevel(log_level)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
    return logger
