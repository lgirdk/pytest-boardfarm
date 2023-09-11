"""pytest plugin for boardfarm."""

import sys

from pytest import Config  # noqa: PT013

from pytest_boardfarm3 import boardfarm_fixtures
from pytest_boardfarm3.boardfarm_plugin import BOARDFARM_PLUGIN_NAME, BoardfarmPlugin

sys.setrecursionlimit(3000)

# pylint: disable=too-few-public-methods


def pytest_load_initial_conftests(early_config: Config, args: list[str]) -> None:
    """Register boardfarm plugin to pytest based on command line arguments.

    :param early_config: pytest config
    :type early_config: Config
    :param args: command line arguments
    :type args: list[str]
    """
    early_config.pluginmanager.register(boardfarm_fixtures)
    if any(x for x in args if x in ("--help", "-h", "--board-name")):
        early_config.pluginmanager.register(BoardfarmPlugin(), BOARDFARM_PLUGIN_NAME)
