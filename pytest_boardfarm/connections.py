from boardfarm.bft import connect_to_devices, logger
from boardfarm.exceptions import BftSysExit
from boardfarm.lib import test_configurator
from termcolor import colored


def bf_connect(config):
    board_type = config.getoption("--bfboard")
    board_type = [
        board_type,
    ]  # convert to list
    board_name = config.getoption("--bfname")
    station_config_loc = config.getoption("--bfconfig_file")
    if not station_config_loc:
        msg = "No inventory file provided (either use env variable or --bfconfig_file)!!!!"
        logger.error(colored(msg, "red"))
        raise BftSysExit(msg)
    env_config_loc = config.getoption("--bfenv_file")
    skip_boot = config.getoption("--bfskip_boot")
    skip_debug_on_fail = config.getoption("--bfskip_debug_on_fail")

    # Get details about available stations (it returns a location
    # in case of redirects)
    # Note: if a file is given the _ridirect will be ingnored
    from_file = not station_config_loc.startswith("http")
    loc, conf = test_configurator.get_station_config(station_config_loc, from_file)

    # Setup test configuration
    test_config = test_configurator.BoardfarmTestConfig()
    test_config.boardfarm_config_location = loc
    test_config.boardfarm_config = conf
    test_config.test_args_location = env_config_loc
    test_config.skip_debug_on_fail = skip_debug_on_fail
    test_config.bf_board_name = board_name
    test_config.bf_board_type = board_type

    test_config.ARM = None
    test_config.ATOM = None
    test_config.COMBINED = None
    # Connect to a station (board and devices)
    return connect_to_devices(test_config) + (skip_boot,)
