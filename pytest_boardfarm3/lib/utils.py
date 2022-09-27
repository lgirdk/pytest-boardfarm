"""Pytest boardfarm utils."""
import sys
from typing import Any, Callable

from _pytest.logging import LoggingPlugin, _remove_ansi_escape_sequences, catching_logs


def is_env_matching(test_env_request: Any, boardfarm_env: Any) -> bool:
    """Check test environment request is a subset of boardfarm environment.

    Recursively checks dictionaries for match. A value of None in the test
    environment request is used as a wildcard, i.e. matches any values.
    A list in test environment request is considered as options in boardfarm
    environment configuration.

    :param test_env_request: test environment request
    :param boardfarm_env: boardfarm environment data
    :return: True if test environment requirements are met, otherwise False
    """
    is_matching = False
    if test_env_request is None:
        is_matching = True
    elif (
        isinstance(test_env_request, dict)
        and isinstance(boardfarm_env, dict)
        and all(
            is_env_matching(v, boardfarm_env.get(k))
            for k, v in test_env_request.items()
        )
    ):
        is_matching = True
    elif (
        isinstance(test_env_request, list)
        and isinstance(boardfarm_env, (str, int, float, bool))
        and boardfarm_env in test_env_request
    ):
        is_matching = True
    elif (
        isinstance(boardfarm_env, list)
        and isinstance(test_env_request, (str, int, float, bool))
        and test_env_request in boardfarm_env
    ):
        is_matching = True
    elif (
        isinstance(test_env_request, dict)
        and isinstance(boardfarm_env, list)
        and any(is_env_matching(test_env_request, item) for item in boardfarm_env)
    ):
        is_matching = True
    elif (
        isinstance(test_env_request, list)
        and isinstance(boardfarm_env, list)
        and all(is_env_matching(item, boardfarm_env) for item in test_env_request)
    ):
        is_matching = True
    elif (
        isinstance(test_env_request, list)
        and isinstance(boardfarm_env, dict)
        and any(is_env_matching(item, boardfarm_env) for item in test_env_request)
    ):
        is_matching = True
    elif test_env_request == boardfarm_env:
        is_matching = True
    return is_matching


def capture_boardfarm_logs(
    logging_plugin: LoggingPlugin, function: Callable, capture_to: dict
) -> None:
    """Capture boardfarm logs on given function execution.

    This method captures the logs to given 'capture_to' dictionary argument.
    Both logs and exceptions are captured to the dictionary with keys 'logs' and
    'exception'. These values will be used for html report generation.

    :param logging_plugin: pytest logging plugin
    :param function: function that requires log capture
    :param capture_to: dictionary instance to save captured logs
    """
    with catching_logs(
        logging_plugin.report_handler, logging_plugin.log_level
    ) as report_logger:
        report_logger.reset()
        try:
            function()
        except:  # noqa: E722,B001 # we capture all exceptions
            capture_to["exception"] = sys.exc_info()
            raise
        finally:
            capture_to["logs"] = _remove_ansi_escape_sequences(
                report_logger.stream.getvalue().strip()
            )
            report_logger.reset()
