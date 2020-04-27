import os

import boardfarm_docsis.lib.booting
import pytest
from boardfarm.bft import connect_to_devices
from boardfarm.lib import test_configurator


def pytest_addoption(parser):
    group = parser.getgroup('boardfarm')
    group.addoption("--bfboard",
                    action="store",
                    default="type1",
                    help="board type")
    group.addoption("--bfconfig_file",
                    action="store",
                    default=None,
                    help="JSON config file for boardfarm devices")
    group.addoption("--bfenv_file",
                    action="store",
                    default=None,
                    help="JSON config file for boardfarm environment")


def save_console_logs(config, device_mgr):
    print("----- Save Console Logs -----")
    # Save console logs
    for idx, console in enumerate(device_mgr.board.consoles, start=1):
        with open(os.path.join(config.output_dir, 'console-%s.log' % idx),
                  'w') as clog:
            clog.write(console.log)
    print("There are %s devices" % len(config.devices))
    for device in config.devices:
        with open(os.path.join(config.output_dir, device + ".log"),
                  'w') as clog:
            d = getattr(config, device)
            if hasattr(d, 'log'):
                clog.write(d.log)


@pytest.fixture(scope="class")
def boardfarm_fixtures(request):
    '''
    Create needed fixtures for boardfarm tests.
    Lab configuration, Device Manager, Environment Config helper
    '''
    board_type = request.config.getoption('--bfboard')
    board_type = [
        board_type,
    ]  # convert to list
    station_config_loc = request.config.getoption('--bfconfig_file')
    env_config_loc = request.config.getoption('--bfenv_file')

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
    test_config.test_args_location = env_config_loc

    # Connect to a station (board and devices)
    config, device_mgr, env_helper, bfweb = connect_to_devices(test_config)

    request.cls.config = config
    request.cls.dev = device_mgr
    request.cls.env_helper = env_helper
    request.cls.reset_after_fail = True
    request.cls.dont_retry = False
    request.cls.logged = dict()
    request.cls.subtests = []
    request.cls.attempts = 0

    try:
        boardfarm_docsis.lib.booting.boot(config=request.cls.config,
                                          env_helper=request.cls.env_helper,
                                          devices=request.cls.dev,
                                          logged=request.cls.logged)
    except Exception:
        save_console_logs(config, device_mgr)
        return

    # End of setup
    yield

    save_console_logs(config, device_mgr)
