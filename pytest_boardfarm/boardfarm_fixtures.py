"""pytest boardfarm fixtures."""

from _pytest.config import Config
from boardfarm.lib.boardfarm_config import BoardfarmConfig
from boardfarm.lib.device_manager import DeviceManager
from pytest import fixture

from pytest_boardfarm.boardfarm_plugin import BOARDFARM_PLUGIN_NAME, BoardfarmPlugin
from pytest_boardfarm.exceptions import BoardfarmPluginError
from pytest_boardfarm.pytest_logging import LogWrapper


class _ContextStorage:  # pylint: disable=too-few-public-methods
    """Context storage class to store test context data."""


@fixture(scope="function")
def bf_context() -> _ContextStorage:
    """Fixture that return context storage instance.

    :return: context storage instance
    """
    return _ContextStorage()


@fixture(scope="session", autouse=True)
def bf_logger() -> LogWrapper:
    """Fixture that return test step log wrapper instance.

    :return: log wrapper instance
    """
    return LogWrapper()


def get_boardfarm_plugin(pytestconfig: Config) -> BoardfarmPlugin:
    """Return boardfarm plugin from pytest config.

    :param pytestconfig: pytest config
    :raises BoardfarmPluginError: when boardfarm plugin is not registered
    :return: boardfarm plugin instance
    """
    plugin = pytestconfig.pluginmanager.get_plugin(BOARDFARM_PLUGIN_NAME)
    if plugin is None:
        raise BoardfarmPluginError("boardfarm plugin is not registered.")
    return plugin


@fixture(scope="session")
def boardfarm_config(pytestconfig: Config) -> BoardfarmConfig:
    """Fixture that return boardfarm config.

    :param pytestconfig: pytest config
    :return: boardfarm config
    """
    return get_boardfarm_plugin(pytestconfig).boardfarm_config


@fixture(scope="session")
def device_manager(pytestconfig: Config) -> DeviceManager:
    """Fixture that return boardfarm device manager.

    :param pytestconfig: pytest config
    :return: boardfarm device manager
    """
    return get_boardfarm_plugin(pytestconfig).device_manager
