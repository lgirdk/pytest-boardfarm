# -*- coding: utf-8 -*-
import os
import time

import pytest
from boardfarm_lgi.lib.lgi_test_lib import PreConditionCheck
from py.xml import html
from termcolor import colored

_ignore_bft = False


def pytest_addoption(parser):
    """Add options to control the boardfarm plugin."""
    group = parser.getgroup(
        "boardfarm", "Allows for the integration of boardfam as a pytest plugin"
    )
    group.addoption("--bfboard", action="store", default="type1", help="board type")
    group.addoption(
        "--bfname",
        action="store",
        default=[],
        help="one or more board names (comma separated)",
    )
    group.addoption(
        "--bfconfig_file",
        action="store",
        default=os.getenv("BFT_CONFIG", None),
        help="JSON config file for boardfarm devices",
    )
    group.addoption(
        "--bfenv_file",
        action="store",
        default=os.getenv("BFT_ARGS", None),
        required=False,
        help="JSON config file for boardfarm environment",
    )
    group.addoption(
        "--bfskip_boot",
        action="store_true",
        default=False,
        help="do not initialise the board (i.e. use it as is)",
    )
    group.addoption(
        "--bffeature",
        action="append",
        default=[],
        help="Features required for this test run",
    )
    group.addoption(
        "--bffilter",
        action="append",
        default=None,
        help="Regex filter off arbitrary board parameters",
    )
    group.addoption(
        "--bfarm",
        action="store",
        default=None,
        help="URL or file PATH of Arm software image to flash.",
    )
    group.addoption(
        "--bfatom",
        action="store",
        default=None,
        help="URL or file PATH of Atom software image to flash.",
    )
    group.addoption(
        "--bfcombined",
        action="store",
        default=None,
        help="URL or file PATH of ARM&ATOM Combined software image to flash.",
    )


@pytest.hookimpl
def pytest_configure(config):
    config.addinivalue_line("markers", "ams_automated_stable_tcs")
    config.addinivalue_line("markers", "bf_lgi_selftest")
    config.addinivalue_line("markers", "bft_released_tests")
    config.addinivalue_line("markers", "Config_File_Testcases")
    config.addinivalue_line("markers", "DUT_Reboot_tcs")
    config.addinivalue_line("markers", "lgirdk_mvx")
    config.addinivalue_line("markers", "release10")
    config.addinivalue_line("markers", "release11")
    config.addinivalue_line("markers", "release12")
    config.addinivalue_line("markers", "release3")
    config.addinivalue_line("markers", "release3_FW_up_downgrade")
    config.addinivalue_line("markers", "release4_FW_up_downgrade")
    config.addinivalue_line("markers", "release5")
    config.addinivalue_line("markers", "release9")
    config.addinivalue_line("markers", "svl_nightly")
    config.addinivalue_line("markers", "svl_nightly_fw")
    config.addinivalue_line("markers", "telemetry_TR069_gpv_datatype_validation")
    config.addinivalue_line("markers", "telemetry_TR069_simple_gpv")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    if call.when == "setup" and hasattr(item.session, "time_to_boot"):
        call.start -= item.session.time_to_boot
        item.session.time_to_boot = 0
    yield


@pytest.mark.tryfirst
def pytest_cmdline_main(config):
    cmdargs = config.invocation_params.args
    if "--bfboard" not in cmdargs:
        global _ignore_bft
        _ignore_bft = True
    elif "--capture=tee-sys" not in cmdargs:
        print(
            colored(
                "Consider using --capture=tee-sys (logging to screen and file)", "red"
            )
        )


def save_console_logs(config, device_mgr):
    print("----- Save Console Logs -----")
    # Save console logs
    for idx, console in enumerate(device_mgr.board.consoles, start=1):
        with open(os.path.join(config.output_dir, "console-%s.log" % idx), "w") as clog:
            clog.write(console.log)
    print("There are %s devices" % len(config.devices))
    for device in config.devices:
        with open(os.path.join(config.output_dir, device + ".log"), "w") as clog:
            d = getattr(config, device)
            if hasattr(d, "log"):
                clog.write(d.log)


def setup_report_info(config, device_mgr, env_helper, bfweb, skip_boot):
    """Helper function that sets a few env variables that will be used to
    enhance the test report
    """
    sw = env_helper.get_software()
    os.environ["BFT_PYTEST_REPORT_IMAGE"] = sw.get("image_uri", "")
    os.environ["BFT_PYTEST_REPORT_BOARDNAME"] = device_mgr.board.config.get_station()
    os.environ["BFT_PYTEST_REPORT_PROV_MODE"] = env_helper.get_prov_mode()
    os.environ["BFT_PYTEST_REPORT_SKIP_BOOT"] = str(skip_boot)


def pytest_html_results_summary(prefix, summary, postfix):
    prefix.extend([html.p(html.b("Image: "), os.getenv("BFT_PYTEST_REPORT_IMAGE", ""))])
    prefix.extend([html.p(html.b("Board: "), os.getenv("BFT_PYTEST_REPORT_BOARDNAME"))])
    prefix.extend(
        [html.p(html.b("Prov Mode: "), os.getenv("BFT_PYTEST_REPORT_PROV_MODE"))]
    )
    if os.getenv("BFT_PYTEST_REPORT_SKIP_BOOT"):
        prefix.extend(
            [html.p(html.b("BOOT Skipped: "), os.getenv("BFT_PYTEST_REPORT_SKIP_BOOT"))]
        )


@pytest.yield_fixture(scope="session")
def boardfarm_fixtures_init(request):
    """Initialisation fixture. Parses the comd line values. If bfboard is found
    attempts connecting to a device and returns the Device Manager, Environment
    Config helper, otherwise the fixture has no effect.
    """
    if not _ignore_bft:
        import boardfarm_docsis.lib.booting
        from boardfarm.bft import connect_to_devices
        from boardfarm.lib import test_configurator

        board_type = request.config.getoption("--bfboard")
        board_type = [
            board_type,
        ]  # convert to list
        board_names = request.config.getoption("--bfname")
        if isinstance(board_names, str):
            board_names = board_names.split(",", -1)
        station_config_loc = request.config.getoption("--bfconfig_file")
        env_config_loc = request.config.getoption("--bfenv_file")
        skip_boot = request.config.getoption("--bfskip_boot")
        features = request.config.getoption("--bffeature")
        board_filter = request.config.getoption("--bffilter")

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

        if features or board_filter:
            print("Boards available are: {}".format(names))

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
        config, device_mgr, env_helper, bfweb = connect_to_devices(test_config)

        config.ARM = request.config.getoption("--bfarm")
        config.ATOM = request.config.getoption("--bfatom")
        config.COMBINED = request.config.getoption("--bfcombined")

        request.session.time_to_boot = 0
        if not skip_boot:
            try:
                t = time.time()
                boardfarm_docsis.lib.booting.boot(
                    config=config,
                    env_helper=env_helper,
                    devices=device_mgr,
                    logged=dict(),
                )
                request.session.time_to_boot = time.time() - t
            except Exception as e:
                print(e)
                save_console_logs(config, device_mgr)
                raise

        yield config, device_mgr, env_helper, bfweb, skip_boot
        setup_report_info(config, device_mgr, env_helper, bfweb, skip_boot)
    else:
        yield

    print("Test session completed")


@pytest.fixture(scope="class", autouse=True)
def boardfarm_fixtures(boardfarm_fixtures_init, request):
    """
    Create needed fixtures for boardfarm tests classes.
    """
    if request.cls and not _ignore_bft:
        from boardfarm.tests import bft_base_test

        # Connect to a station (board and devices)
        config, device_mgr, env_helper, bfweb, skip_boot = boardfarm_fixtures_init
        request.cls.config = config
        request.cls.dev = device_mgr
        request.cls.env_helper = env_helper
        request.cls.reset_after_fail = True
        request.cls.dont_retry = False
        request.cls.logged = dict()
        request.cls.subtests = []
        request.cls.attempts = 0
        # the mother of all hacks
        bft_base_test.BftBaseTest.__init__(
            request.instance, config, device_mgr, env_helper
        )

        # End of setup
        yield

        if request.cls.test_obj and "FAIL" in request.cls.test_obj.result_grade:
            PreConditionCheck._cache_contingency = -1

        save_console_logs(config, device_mgr)
    else:
        yield


@pytest.fixture
def devices(boardfarm_fixtures_init):
    """Fixture that returs the connected devices"""
    yield boardfarm_fixtures_init[1]


@pytest.fixture
def env_helper(boardfarm_fixtures_init):
    """Fixture that returns the Environment Helper"""
    yield boardfarm_fixtures_init[2]


@pytest.fixture
def config(boardfarm_fixtures_init):
    """Fixture that returns the currenet Config"""
    yield boardfarm_fixtures_init[0]
