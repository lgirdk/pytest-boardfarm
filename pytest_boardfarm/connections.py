from boardfarm.bft import connect_to_devices, logger
from boardfarm.exceptions import BftSysExit
from boardfarm.lib import test_configurator
from termcolor import colored


def bf_connect(config):
    board_type = config.getoption("--bfboard")
    board_type = [
        board_type,
    ]  # convert to list
    board_names = config.getoption("--bfname")
    if isinstance(board_names, str):
        board_names = board_names.split(",", -1)
    station_config_loc = config.getoption("--bfconfig_file")
    env_config_loc = config.getoption("--bfenv_file")
    skip_boot = config.getoption("--bfskip_boot")
    features = config.getoption("--bffeature")
    board_filter = config.getoption("--bffilter")

    # Get details about available stations (it returns a location
    # in case of redirects)
    # Note: if a file is given the _ridirect will be ingnored
    from_file = not station_config_loc.startswith("http")
    loc, conf = test_configurator.get_station_config(station_config_loc, from_file)

    # Find available stations with compatible boards (DUTs)
    names = test_configurator.filter_station_config(
        conf,
        board_type=board_type,
        board_names=board_names,
        board_features=features,
        board_filter=board_filter,
    )

    if names:
        logger.info(
            colored(f"Boards available are: {names}", color="green", attrs=["bold"])
        )
    else:
        msg = "No boards available!!!!"
        logger.error(colored(msg, "red"))
        raise BftSysExit(msg)

    # Setup test configuration
    test_config = test_configurator.BoardfarmTestConfig()
    test_config.BOARD_NAMES = names
    test_config.boardfarm_config_location = loc
    test_config.boardfarm_config = conf
    test_config.test_args_location = env_config_loc

    test_config.ARM = None
    test_config.ATOM = None
    test_config.COMBINED = None
    # Connect to a station (board and devices)
    return connect_to_devices(test_config) + (skip_boot,)
