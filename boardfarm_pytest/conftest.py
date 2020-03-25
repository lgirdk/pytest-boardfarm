import os
import pexpect
import pytest

from boardfarm.bft import connect_to_devices
from boardfarm.lib import test_configurator


def pytest_addoption(parser):
    parser.addoption("--board",
                     action="store",
                     default="type1",
                     help="board type")
    parser.addoption("--config_file",
                     action="store",
                     default=None,
                     help="JSON config file for boardfarm")
    parser.addoption("--testsuite",
                     action="store",
                     default="connect",
                     help="suite of tests to run")


@pytest.fixture(scope="class")
def standard(request):
    '''
    Create needed fixtures for boardfarm tests.
    '''
    board_type = request.config.getoption('--board')
    board_type = [board_type,]  # convert to list
    station_config_loc = request.config.getoption('--config_file')
    testsuite = request.config.getoption('--testsuite')

    # Get details about available stations (it returns a location
    # in case of redirects)
    loc, conf = test_configurator.get_station_config(station_config_loc)

    # Find available stations with compatible boards (DUTs)
    names = test_configurator.filter_station_config(conf,
                                                    board_type=board_type)

    # Setup test configuration
    test_config = test_configurator.BoardfarmTestConfig()
    test_config.BOARD_NAMES = names
    test_config.boardfarm_config_location = loc
    test_config.boardfarm_config = conf

    ## Connect to a station (board and devices)
    #config, device_mgr, env_helper, bfweb = connect_to_devices(test_config)

    #request.cls.config = config
    #request.cls.dev = device_mgr
    #request.cls.env_helper = env_helper
    #request.cls.reset_after_fail = True
    #request.cls.dont_retry = False
    #request.cls.logged = dict()
    #request.cls.subtests = []
    #request.cls.attempts = 0
