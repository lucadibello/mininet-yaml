from datetime import datetime
import logging
import os

from modules.util.singleton import Singleton


class Logger(metaclass=Singleton):
    """
    Sigleton class that creates a logger object that logs to a file and the console.
    """

    def __init__(self, dir: str = "log"):
        if not isinstance(dir, str):
            raise TypeError("the directory must be a string.")

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)  # Set the log level to DEBUG

        # Generate a filename using basename+timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        # Format the filename
        os.makedirs(dir, exist_ok=True)
        filename = os.path.join(dir, f"emulation_{timestamp}.log")

        # Create a file handler which logs even debug messages
        fh = logging.FileHandler(filename)
        fh.setLevel(logging.DEBUG)

        # Create a console handler which logs messages to the console
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # Create a formatter and set the formatter for the handlers
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # Add the handlers to the logger
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str):
        self.logger.error(message)

    def fatal(self, message: str):
        self.logger.fatal(message)
        exit(1)
