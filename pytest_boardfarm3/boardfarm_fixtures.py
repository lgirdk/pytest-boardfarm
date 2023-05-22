"""pytest boardfarm fixtures."""

from argparse import Namespace
from typing import Any

import pytest
from _pytest.config import Config
from boardfarm3.devices.base_devices import BoardfarmDevice
from boardfarm3.lib.boardfarm_config import BoardfarmConfig
from boardfarm3.lib.device_manager import DeviceManager

from pytest_boardfarm3.boardfarm_plugin import BOARDFARM_PLUGIN_NAME, BoardfarmPlugin
from pytest_boardfarm3.exceptions import BoardfarmPluginError
from pytest_boardfarm3.lib.test_logger import TestLogger
from pytest_boardfarm3.lib.utils import ContextStorage


@pytest.fixture(scope="function")
def bf_context() -> ContextStorage:
    """Fixture that return context storage instance.

    :return: context storage instance
    :rtype: ContextStorage
    """
    return ContextStorage()


@pytest.fixture(scope="session", autouse=True)
def bf_logger() -> TestLogger:
    """Fixture that return test step log wrapper instance.

    :return: log wrapper instance
    :rtype: TestLogger
    """
    return TestLogger()


def get_boardfarm_plugin(pytestconfig: Config) -> BoardfarmPlugin:
    """Return boardfarm plugin from pytest config.

    :param pytestconfig: pytest config
    :type pytestconfig: Config
    :raises BoardfarmPluginError: when boardfarm plugin is not registered
    :return: boardfarm plugin instance
    :rtype: BoardfarmPlugin
    """
    plugin = pytestconfig.pluginmanager.get_plugin(BOARDFARM_PLUGIN_NAME)
    if plugin is None:
        err_msg = "boardfarm plugin is not registered."
        raise BoardfarmPluginError(err_msg)
    return plugin


@pytest.fixture(scope="session")
def boardfarm_config(pytestconfig: Config) -> BoardfarmConfig:
    """Fixture that return boardfarm config.

    :param pytestconfig: pytest config
    :type pytestconfig: Config
    :return: boardfarm config
    :rtype: BoardfarmConfig
    """
    return get_boardfarm_plugin(pytestconfig).boardfarm_config


@pytest.fixture(scope="session")
def device_manager(pytestconfig: Config) -> DeviceManager:
    """Fixture that return boardfarm device manager.

    :param pytestconfig: pytest config
    :param pytestconfig: pytest config
    :return: boardfarm device manager
    :rtype: DeviceManager
    """
    return get_boardfarm_plugin(pytestconfig).device_manager


@pytest.fixture(scope="session")
def devices(
    device_manager: DeviceManager,  # pylint: disable=redefined-outer-name
) -> Any:  # noqa: ANN401
    """Legacy boardfarm devices fixture.

    :param device_manager: device manager
    :type device_manager: DeviceManager
    :return: devices fixture
    :rtype: Any
    """
    return Namespace(**device_manager.get_devices_by_type(BoardfarmDevice))
