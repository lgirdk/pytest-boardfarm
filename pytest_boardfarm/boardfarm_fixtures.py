"""pytest boardfarm fixtures."""

import logging
from typing import Generator

from _pytest.config import Config
from boardfarm.lib.boardfarm_config import BoardfarmConfig
from boardfarm.lib.device_manager import DeviceManager
from boardfarm.templates.lan import LAN
from boardfarm_docsis.templates.cable_modem import CableModem
from boardfarm_lgi_shared.lib.gui.gui_helper import get_web_driver
from pytest import fixture

from pytest_boardfarm.boardfarm_plugin import BOARDFARM_PLUGIN_NAME, BoardfarmPlugin
from pytest_boardfarm.exceptions import BoardfarmPluginError
from pytest_boardfarm.lib.test_logger import TestLogger

_LOGGER = logging.getLogger(__name__)


class ContextStorage:  # pylint: disable=too-few-public-methods
    """Context storage class to store test context data."""


@fixture(scope="function")
def bf_context() -> ContextStorage:
    """Fixture that return context storage instance.

    :return: context storage instance
    """
    return ContextStorage()


@fixture(scope="session", autouse=True)
def bf_logger() -> TestLogger:
    """Fixture that return test step log wrapper instance.

    :return: log wrapper instance
    """
    return TestLogger()


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


@fixture(scope="function")
def browser_data(
    device_manager: DeviceManager, boardfarm_config: BoardfarmConfig
) -> Generator:
    # pylint: disable=redefined-outer-name
    """Provide selenium driver data to tests.

    :param device_manager: device manager fixture
    :param boardfarm_config: boardfarm_config fixture
    :return: initialized webdriver instance, gateway IP and GUI password
    """
    lan = device_manager.get_device_by_type(LAN)
    board = device_manager.get_device_by_type(CableModem)
    driver = get_web_driver(lan)
    # Set board SKU and board hardware type as driver properties
    # to be able to customize POM
    driver.sku = boardfarm_config.get_board_sku()
    driver.board_model = boardfarm_config.get_board_model()
    _LOGGER.info("Initialized %s %s webdriver.", driver.sku, driver.board_model)

    gateway_ipv4 = (
        board.lan_private_gateway
        if boardfarm_config.get_prov_mode() == "disabled"
        else board.lan_gateway
    )

    yield driver, gateway_ipv4, board.gui_password
    driver.quit()
