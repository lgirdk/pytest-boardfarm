import logging

from boardfarm.lib.common import get_pytest_name


class LogWrapper:
    def __init__(self):
        self._logger = logging.getLogger("tests_logger")

    def log_step(self, msg):
        """Prints customised logs to console"""
        testname = get_pytest_name().split("_(")[0]
        self._logger.info(
            "[*****LOGGING-STEP*****]" + "[" + testname + "]" + "[" + msg + "]"
        )
