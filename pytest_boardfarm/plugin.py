# -*- coding: utf-8 -*-
import os
import time

import pytest
from _pytest.config import ExitCode
from boardfarm.bft import logger
from boardfarm.exceptions import BftEnvMismatch, BftSysExit
from boardfarm.lib.bft_logging import write_test_log
from py.xml import html
from termcolor import colored

from pytest_boardfarm.connections import bf_connect
from pytest_boardfarm.tst_results import (
    add_test_result,
    save_results_to_file,
    save_results_to_html_file,
    save_station_to_file,
    send_results_to_elasticsearch,
)

_ignore_bft = False


def get_result_dir():
    owrt_tests_dir = os.path.join(os.getcwd(), "results", "")
    if not os.path.exists(owrt_tests_dir):
        os.makedirs(owrt_tests_dir)
    return owrt_tests_dir


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
    group.addoption(
        "--bfoutput_dir",
        action="store",
        default=get_result_dir(),
        help="Directory for the output results files",
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    if call.when == "setup":
        if hasattr(item.session, "time_to_boot"):
            call.start -= item.session.time_to_boot
            item.session.time_to_boot = 0
    yield
    if call.when == "call" and item.cls is None:
        # this is a pytest test (i.e. a function)
        add_test_result(item, call)
        save_results_to_file()
    if call.when == "teardown" and item.cls:
        add_test_result(item, call)
        save_results_to_file()
        if (
            hasattr(item, "cls")
            and hasattr(item.cls, "test_obj")
            and hasattr(item.cls.test_obj, "log_to_file")
            and hasattr(item.cls.test_obj, "result_grade")
        ):
            write_test_log(item.cls.test_obj, get_result_dir())


def pytest_runtest_call(item):
    env_request = [mark.args[0] for mark in item.iter_markers(name="env_req")]
    if hasattr(item.session, "env_helper") and env_request:
        try:
            item.session.env_helper.env_check(env_request[0])
        except BftEnvMismatch:
            pytest.skip("Environment mismatch. Skipping")


def pytest_sessionfinish(session, exitstatus):
    if hasattr(session, "bft_config"):
        save_results_to_html_file(session.bft_config)
        send_results_to_elasticsearch(session.bft_config)


@pytest.mark.tryfirst
def pytest_cmdline_main(config):
    cmdargs = config.invocation_params.args
    if "--bfboard" not in cmdargs:
        global _ignore_bft
        _ignore_bft = True

    if not _ignore_bft and "--bfconfig_file" in cmdargs and "--bfname" not in cmdargs:
        msg = "If overriding the dashboard from cli a board name MUST be given"
        logger.error(colored(msg, "red", attrs=["bold"]))
        pytest.exit(msg=msg, returncode=ExitCode.USAGE_ERROR)

    if not _ignore_bft and "--capture=tee-sys" not in cmdargs:
        msg = "Consider using --capture=tee-sys (logging to screen and file)"
        logger.info(colored(msg, "yellow"))


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
    if os.getenv("BFT_PYTEST_BOOT_FAILED"):
        prefix.extend([html.p(html.b("--==** FAILED ON BOOT **==--"))])
    elif os.getenv("BFT_PYTEST_REPORT_SKIP_BOOT"):
        prefix.extend(
            [html.p(html.b("BOOT Skipped: "), os.getenv("BFT_PYTEST_REPORT_SKIP_BOOT"))]
        )


@pytest.yield_fixture(scope="session")
def boardfarm_fixtures_init(request):
    """Initialisation fixture. Parses the cmd line values. If bfboard is found
    attempts connecting to a device and returns the Device Manager, Environment
    Config helper, otherwise the fixture has no effect.
    """
    import boardfarm_docsis.lib.booting

    if not _ignore_bft:
        try:
            config, device_mgr, env_helper, bfweb, skip_boot = bf_connect(
                request.config
            )
        except (BftSysExit, SystemExit) as e:
            os.environ[
                "BFT_PYTEST_REPORT_BOARDNAME"
            ] = f"Could not connect to any boards ({repr(e)})"
            pytest.exit(e)
        except Exception as e:
            msg = f"Unhandled exception on connection: {repr(e)}"
            logger.error(msg)
            os.environ["BFT_PYTEST_REPORT_BOARDNAME"] = msg
            pytest.exit(e)

        # save station name to file
        save_station_to_file(device_mgr.board.config.get_station())

        config.ARM = request.config.getoption("--bfarm")
        config.ATOM = request.config.getoption("--bfatom")
        config.COMBINED = request.config.getoption("--bfcombined")
        setup_report_info(config, device_mgr, env_helper, bfweb, skip_boot)
        request.session.time_to_boot = 0
        request.session.bft_config = config
        request.session.env_helper = env_helper
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
                os.environ["BFT_PYTEST_BOOT_FAILED"] = str(skip_boot)
                pytest.exit("BFT_PYTEST_BOOT_FAILED")

        yield config, device_mgr, env_helper, bfweb, skip_boot
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

        try:
            from boardfarm_lgi.lib.lgi_test_lib import PreConditionCheck

            if (
                request.cls.test_obj
                and hasattr(request.cls.test_obj, "result_grade")
                and "FAIL" in request.cls.test_obj.result_grade
            ):
                PreConditionCheck._cache_contingency = -1
        except ImportError:
            pass

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
