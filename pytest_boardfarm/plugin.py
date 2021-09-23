import os
import re
import sys
import time
import traceback
import unicodedata
from datetime import datetime
from pathlib import Path

import boardfarm_docsis.lib.booting
import pytest
from _pytest.config import Config, ExitCode
from boardfarm.bft import logger
from boardfarm.exceptions import BftEnvMismatch, BftSysExit, ContingencyCheckError
from boardfarm.lib.bft_logging import write_test_log
from boardfarm.tests import bft_base_test
from py.xml import html  # pylint: disable=no-name-in-module,import-error
from tabulate import tabulate
from termcolor import colored

from pytest_boardfarm.connections import bf_connect
from pytest_boardfarm.hooks import contingency_check
from pytest_boardfarm.pytest_logging import LogWrapper
from pytest_boardfarm.tst_results import add_test_result, save_station_to_file

sys.setrecursionlimit(3000)

this = sys.modules[__name__]

this.DEVICES = None
this.ENV_HELPER = None
this.BF_WEB = None
this.CONFIG = None
this.SKIPBOOT = None
this.IGNORE_BFT = False
this.BFT_CONNECT = False
this.IP = {}
this.PYTESTCONFIG = None
this.CUSTOM_EXITCODES = {
    200: "failed on boot",
    201: "could not find any board",
}


def get_result_dir():
    owrt_tests_dir = os.path.join(os.getcwd(), "results", "")
    if not os.path.exists(owrt_tests_dir):
        os.makedirs(owrt_tests_dir)
    return owrt_tests_dir


def get_debug_info_dir(test_name):
    debug_info_dir = os.path.join(get_result_dir(), test_name + "_debug_info")
    if not os.path.exists(debug_info_dir):
        os.makedirs(debug_info_dir)
    return debug_info_dir


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "env_req(env_req: Dict): mark test with environment request. Skip"
        " test if environment check fails.\n"
        'Example: @pytest.mark.env_req({"environment_def":{"board":'
        '{"eRouter_Provisioning_mode":["dual"]}}})',
    )


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
        default=os.getenv("BFT_FEATURES").split(",")
        if os.getenv("BFT_FEATURES")
        else [],
        help="Features required for this test run",
    )
    group.addoption(
        "--bffilter",
        action="append",
        default=os.getenv("BFT_FILTERS"),
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
    group.addoption(
        "--bfskip_contingency",
        action="store_true",
        default=False,
        help="do not perform ANY env/contingency checks when running tests"
        " (useful when running from the interact menu)",
    )
    group.addoption(
        "--bfskip_debug_on_fail",
        action="store_true",
        default=False,
        help="Flag to skip debug logs collection on each fail.",
    )


def trim_pytest_result_for_email(filepathin, filepathout):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(open(filepathin), "html.parser")

    # remove the log text that can be in the Megabytes
    for div in soup.find_all("div", {"class": "log"}):
        div.decompose()
    # remove the text (Un)check the boxes to filter the results
    soup.find("p", class_="filter").decompose()
    # remove the text No results found. Try to check the filters
    for t in soup.find_all("tr", id="not-found-message"):
        check = t.find("th", colspan="4")
        if check is not None:
            t.decompose()

    # saves the stripped down page
    with open(filepathout, "w") as file:
        file.write(str(soup))


def __set_cache_ips():
    """Transitional helper now that the contingencies are run in the setup
    fixture. This method will eventually be removed."""

    try:
        from boardfarm_lgi.lib.lgi_test_lib import PreConditionCheck

        PreConditionCheck.__cache_ips__ = this.IP
    except ImportError:
        pass


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_setup(item):

    env_req = None
    # starttime and stationid properties are added under the properties tag of the result XML
    # which is then used by the draw_timeline.py
    item.user_properties.append(("starttime", time.time()))
    item.user_properties.append(("stationid", os.getenv("BFT_PYTEST_REPORT_BOARDNAME")))
    has_env_marker = [mark.args[0] for mark in item.iter_markers(name="env_req")]
    if (
        hasattr(item, "cls")
        and item.cls
        and issubclass(item.cls, bft_base_test.BftBaseTest)
    ):
        bft_base_test.BftBaseTest.dev = this.DEVICES
        bft_base_test.BftBaseTest.config = this.CONFIG
        bft_base_test.BftBaseTest.env_helper = this.ENV_HELPER
        if hasattr(item.cls, "env_req"):
            env_req = item.cls.env_req

    if not env_req:
        env_req = has_env_marker[0] if has_env_marker else {}
    if (
        (env_req or item.name == "test_main")
        and this.PYTESTCONFIG.getoption("--bfskip_contingency") is False
        and this.ENV_HELPER
        and "interact" not in item.name.lower()
    ):
        try:
            this.ENV_HELPER.env_check(env_req)
        except BftEnvMismatch:
            pytest.skip("Environment mismatch. Skipping")
        try:
            this.IP = contingency_check(env_req, this.DEVICES, this.ENV_HELPER)
            __set_cache_ips()
        except Exception as exc:
            # assuming stack trace is printed by internal hooks
            traceback.print_exc()
            raise ContingencyCheckError(f"CC FAIL: {str(exc)}\nAborting")

    yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item):

    if os.environ.get("BFT_ELASTICSERVER", None) is None:
        msg = [
            "\nElasticsearch Server is not Configured",
            "Configure Elasticsearch Server by executing",
            "following command in shell\n",
            '$ export BFT_ELASTICSERVER="http://10.64.38.15:9200"',
        ]

        raise Exception(colored("\n".join(msg), "red", attrs=["bold"]))

    elk_reporter = item.config.pluginmanager.get_plugin("elk-reporter-runtime")
    configure_elk(elk_reporter)

    if not this.IGNORE_BFT and not this.BFT_CONNECT:
        try:
            config, device_mgr, env_helper, bfweb, skip_boot = bf_connect(item.config)
            this.DEVICES = device_mgr
            this.CONFIG = config
            this.ENV_HELPER = env_helper
            this.BF_WEB = bfweb
            this.SKIPBOOT = skip_boot
        except (BftSysExit, SystemExit) as e:
            os.environ[
                "BFT_PYTEST_REPORT_BOARDNAME"
            ] = f"Could not connect to any boards ({repr(e)})"
            pytest.exit(msg=this.CUSTOM_EXITCODES[201], returncode=201)
        except Exception as e:
            traceback.print_exc()
            msg = f"Unhandled exception on connection: {repr(e)}"
            logger.error(msg)
            os.environ["BFT_PYTEST_REPORT_BOARDNAME"] = msg
            pytest.exit(msg=this.CUSTOM_EXITCODES[201], returncode=201)

        # save station name to file
        save_station_to_file(this.DEVICES.board.config.get_station())
        setup_report_info(
            config, this.DEVICES, this.ENV_HELPER, this.BF_WEB, this.SKIPBOOT
        )
        # so this does not run again on every loop
        this.BFT_CONNECT = True

        item.session.time_to_boot = 0
        item.session.bft_config = this.CONFIG
        item.session.env_helper = this.ENV_HELPER
        item.session.html_report_file = item.config.getoption("--html", "")

        if not this.ENV_HELPER.has_board_sku():
            warning_message = (
                "Board SKU/CustomerId is not found in board.SKU or boot_file inside of env.json."
                "\nCustomerId TLV won't be set in docsis boot file"
            )
            logger.warning(
                colored(tabulate([[warning_message]]), color="red", attrs=["bold"])
            )

        if not this.SKIPBOOT:
            try:
                t = time.time()
                boardfarm_docsis.lib.booting.boot(
                    config=this.CONFIG,
                    env_helper=this.ENV_HELPER,
                    devices=this.DEVICES,
                    logged=dict(),
                )
                item.session.time_to_boot = time.time() - t
            except Exception as e:
                logger.error(colored(e, color="red", attrs=["bold"]))
                save_console_logs(this.CONFIG, this.DEVICES)
                os.environ["BFT_PYTEST_BOOT_FAILED"] = str(this.SKIPBOOT)
                pytest.exit(msg=this.CUSTOM_EXITCODES[200], returncode=200)

    yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    if call.when == "setup" and hasattr(item.session, "time_to_boot"):
        call.start -= item.session.time_to_boot
        item.session.time_to_boot = 0
    outcome = yield

    report = outcome.get_result()
    report.test_start_time = call.start

    if call.when == "call" and item.cls is None:
        # this is a pytest test (i.e. a function)
        add_test_result(item, call)
    if (
        call.when == "call"
        and report.failed
        and this.DEVICES  # We are not in unit tests
        and not this.CONFIG.skip_debug_on_fail  # Skip flag is not set
    ):
        # Collect debug info after failed test
        logger.info(
            "\nDetected failed test. Collecting debug info. "
            "\nAdd --bfskip_debug_on_fail flag to skip this."
        )
        try:
            start = time.time()
            debug_file_name = os.path.join(
                get_debug_info_dir(item.name), "debug_logs.txt"
            )
            with open(debug_file_name, "w") as debug_log_file:
                for output in this.DEVICES.board.collect_debug_info():
                    debug_log_file.write(output)

            logger.info(
                f"\nDebug info collection took {int(time.time() - start)} "
                "seconds to finish. Add --bfskip_debug_on_fail flag to skip this."
            )
        except Exception as e:
            logger.error(f"Unable to collect debug info: {str(e)}")
    if call.when == "teardown" and item.cls:
        add_test_result(item, call)
        if (
            hasattr(item, "cls")
            and hasattr(item.cls, "test_obj")
            and hasattr(item.cls.test_obj, "log_to_file")
            and hasattr(item.cls.test_obj, "result_grade")
        ):
            write_test_log(item.cls.test_obj, get_result_dir())


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_header(cells):
    cells.insert(0, html.th("Start Time", class_="sortable time", col="time"))


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_row(report, cells):
    if "CC FAIL" in report.longreprtext:
        cells[0] = html.td("CC FAIL", class_="col-result")

    test_start_time = datetime.fromtimestamp(report.test_start_time).strftime(
        "%d-%m-%Y %H:%M:%S:%f"
    )
    cells.insert(0, html.td(test_start_time, class_="col-time"))


def pytest_sessionfinish(session, exitstatus):
    if hasattr(session, "bft_config"):
        report_pytestrun_to_elk(session)
    if getattr(session, "html_report_file", None):
        source = session.html_report_file
        dest = os.path.dirname(source) + "/mail_" + os.path.basename(source)
        trim_pytest_result_for_email(source, dest)


def pytest_unconfigure(config: Config) -> None:
    if config.option.xmlpath is None:
        return
    xml_path = Path(config.option.xmlpath)
    if xml_path.exists():
        raw_xml_path = Path(xml_path.parent, "raw_" + xml_path.name)
        xml_content = xml_path.read_text()
        xml_path.rename(raw_xml_path)
        # Remove escape chars and control chars from report.xml file
        escape_chars_regex = r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
        xml_content = re.sub(escape_chars_regex, "", xml_content)
        xml_content = "".join(
            ch
            for ch in xml_content
            if ch in "\n\r" or unicodedata.category(ch)[0] != "C"
        )
        Path(config.option.xmlpath).write_text(xml_content)


@pytest.mark.tryfirst
def pytest_cmdline_main(config):
    def _exists(needle, haystack):
        return any(needle in str_ for str_ in haystack)

    cmdargs = config.invocation_params.args
    if _exists("--bfboard", cmdargs) is False:
        this.IGNORE_BFT = True

    if not this.IGNORE_BFT:
        config.ARM = config.getoption("--bfarm")
        config.ATOM = config.getoption("--bfatom")
        config.COMBINED = config.getoption("--bfcombined")

        if (
            _exists("--bfconfig_file", cmdargs)
            and _exists("--bfname", cmdargs) is False
        ):
            msg = "If overriding the dashboard from cli a board name MUST be given"
            logger.error(colored(msg, "red", attrs=["bold"]))
            pytest.exit(msg=msg, returncode=ExitCode.USAGE_ERROR)

    if not this.IGNORE_BFT and "--capture=tee-sys" not in cmdargs:
        msg = "Consider using --capture=tee-sys (logging to screen and file)"
        logger.info(colored(msg, "yellow"))
    this.PYTESTCONFIG = config


def save_console_logs(config, device_mgr):
    print("----- Save Console Logs -----")
    # Save console logs
    for idx, console in enumerate(device_mgr.board.consoles, start=1):
        with open(os.path.join(config.output_dir, f"console-{idx}.log"), "w") as clog:
            clog.write(console.log)
    print(f"There are {len(config.devices)} devices")
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
    if "image_uri" in sw:
        image_name = sw.get("image_uri")
    elif "load_image" in sw:
        image_name = sw.get("load_image")
    else:
        image_name = "Image not specified"
    os.environ["BFT_PYTEST_REPORT_IMAGE"] = image_name
    os.environ["BFT_PYTEST_REPORT_BOARDNAME"] = config.board.get_station()
    if hasattr(env_helper, "get_prov_mode"):
        os.environ["BFT_PYTEST_REPORT_PROV_MODE"] = env_helper.get_prov_mode()
    os.environ["BFT_PYTEST_REPORT_SKIP_BOOT"] = str(skip_boot)


def __get_randomly_seed():
    seed = None
    try:
        seed = this.PYTESTCONFIG.getoption("--randomly-seed")
    except ValueError:
        msg = colored(
            "Failed to get randomly-seed, plugin disabled or not installed",
            "yellow",
            attrs=["bold"],
        )
        logger.error(msg)
    return seed


def pytest_html_results_summary(prefix, summary, postfix):
    prefix.extend([html.p(html.b("Image: "), os.getenv("BFT_PYTEST_REPORT_IMAGE", ""))])
    prefix.extend([html.p(html.b("Board: "), os.getenv("BFT_PYTEST_REPORT_BOARDNAME"))])
    prefix.extend(
        [html.p(html.b("Prov Mode: "), os.getenv("BFT_PYTEST_REPORT_PROV_MODE"))]
    )

    seed = __get_randomly_seed()
    if seed:
        prefix.extend([html.p(html.b("Randomly Seed Value: "), str(seed))])

    if os.getenv("BFT_PYTEST_BOOT_FAILED"):
        prefix.extend([html.p(html.b("--==** FAILED ON BOOT **==--"))])
    elif os.getenv("BFT_PYTEST_REPORT_SKIP_BOOT"):
        prefix.extend(
            [html.p(html.b("BOOT Skipped: "), os.getenv("BFT_PYTEST_REPORT_SKIP_BOOT"))]
        )


@pytest.fixture(scope="session")
def boardfarm_fixtures_init(request):
    """Initialisation fixture. Parses the cmd line values. If bfboard is found
    attempts connecting to a device and returns the Device Manager, Environment
    Config helper, otherwise the fixture has no effect.
    """
    if not this.IGNORE_BFT:
        yield this.CONFIG, this.DEVICES, this.ENV_HELPER, this.BF_WEB, this.SKIPBOOT
    else:
        yield

    print("\nTest session completed")


@pytest.fixture(scope="class", autouse=True)
def boardfarm_fixtures(boardfarm_fixtures_init, request):
    """
    Create needed fixtures for boardfarm tests classes.
    """
    if request.cls and not this.IGNORE_BFT:
        # Connect to a station (board and devices)
        config, device_mgr, env_helper, bfweb, skip_boot = boardfarm_fixtures_init
        request.cls.config = config
        request.cls.dev = device_mgr
        request.cls.env_helper = env_helper
        request.cls.reset_after_fail = True
        request.cls.dont_retry = False
        request.cls.logged = {}
        request.cls.subtests = []
        request.cls.attempts = 0
        # the mother of all hacks
        bft_base_test.BftBaseTest.__init__(
            request.instance, config, device_mgr, env_helper
        )

        # End of setup
        yield

        save_console_logs(config, device_mgr)
    else:
        yield


@pytest.fixture(scope="session")
def devices():
    """Fixture that returs the connected devices"""
    yield this.DEVICES


@pytest.fixture(scope="session")
def env_helper():
    """Fixture that returns the Environment Helper"""
    yield this.ENV_HELPER


@pytest.fixture(scope="session")
def config():
    """Fixture that returns the current Config"""
    yield this.CONFIG


@pytest.fixture
def interface_ip():
    """Fixture that returns the interface IP's"""
    yield this.IP


def configure_elk(elk_reporter):
    elk_reporter.es_index_name = "boardfarmrun"
    # this is missing from the elk plugin dicitonary
    if not elk_reporter.stats.get("xfailed & error", None):
        elk_reporter.stats.update({"xfailed & error": 0})
    elk_reporter.session_data.update(
        {
            "build_url": os.environ.get("BUILD_URL", None),
            "test_ids": [],
            "test_time": [],
        }
    )
    # set pytest verbose level 2 to stop executing elk-reporter pytest_terminal_summary
    elk_reporter.config.option.verbose = 2


def report_pytestrun_to_elk(session):
    """
    send pytest test run information to elk
    """
    if not session.bft_config.elasticsearch_server:
        return

    session.config.elk.es_address = session.bft_config.elasticsearch_server

    keys = ["build_url", "username", "hostname", "session_start_time"]
    test_data = {k: session.config.elk.session_data[k] for k in keys}
    test_data["board_id"] = os.environ.get("BFT_PYTEST_REPORT_BOARDNAME", None)

    for i, id in enumerate(session.config.elk.session_data["test_ids"]):
        test_data["test_start_time"] = session.config.elk.session_data["test_time"][i][
            0
        ]
        test_data["test_end_time"] = session.config.elk.session_data["test_time"][i][1]
        test_data["test_id"] = "Manual" if "Interact" in id else id
        logger.info(f"Logging Data to ELK: {test_data}")
        session.config.elk.post_to_elasticsearch(test_data)


@pytest.fixture(scope="module", autouse=True)
def bf_logger():
    """Returns wrapper around logging library"""
    return LogWrapper()


@pytest.fixture(scope="function")
def bf_context():
    """Provide dummy object to store test context."""

    class ContextStorage:
        """Object to store context.
        Can be expanded to implement business needs.
        """

        def __init__(self):
            pass

    yield ContextStorage()
