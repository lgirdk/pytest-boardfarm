import logging


class LogWrapper:
    def __init__(self):
        self._logger = logging.getLogger("tests_logger")

    def log_step(self, msg):
        """Prints customised logs to console"""
        self._logger.info("[*****LOGGING-STEP*****]" + "[" + msg + "]")
