"""pytest boardfarm plugin module."""
from collections.abc import Generator
from datetime import datetime
from typing import Optional

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.logging import LoggingPlugin
from _pytest.main import Session
from _pytest.nodes import Item
from _pytest.reports import TestReport
from boardfarm3.lib.boardfarm_config import BoardfarmConfig, parse_boardfarm_config
from boardfarm3.lib.device_manager import DeviceManager, get_device_manager
from boardfarm3.main import get_plugin_manager
from py.xml import Tag, html  # pylint: disable=no-name-in-module,import-error

from pytest_boardfarm3.lib.argument_parser import ArgumentParser
from pytest_boardfarm3.lib.html_report import get_boardfarm_html_table_report
from pytest_boardfarm3.lib.utils import capture_boardfarm_logs, is_env_matching

BOARDFARM_PLUGIN_NAME = "_boardfarm"


class BoardfarmPlugin:
    """Pytest boardfarm plugin."""

    # pylint: disable=no-member  # hook calls are not a member

    def __init__(self) -> None:
        """Initialize boardfarm plugin."""
        self._session_config: Config = None
        self._test_start_time: datetime = None
        self._deployment_setup_data: dict = {}
        self._deployment_teardown_data: dict = {}
        self._plugin_manager = get_plugin_manager()
        self.device_manager: DeviceManager = None
        self.boardfarm_config: BoardfarmConfig = None

    def pytest_addoption(self, parser: Parser) -> None:
        """Add command line arguments to pytest.

        :param parser: argument parser
        :type parser: Parser
        """
        self._plugin_manager.hook.boardfarm_add_cmdline_args(
            argparser=ArgumentParser(parser)
        )

    def deploy_boardfarm_devices(self) -> None:
        """Deploy boardfarm devices to the environment."""
        self.device_manager = self._plugin_manager.hook.boardfarm_deploy_devices(
            config=self.boardfarm_config,
            cmdline_args=self._session_config.option,
            plugin_manager=self._plugin_manager,
        )

    def release_boardfarm_devices(self) -> None:
        """Release boardfarm devices after the test execution."""
        deployment_status = (
            {"status": "success"}
            if "exception" not in self._deployment_setup_data
            else {
                "status": "failed",
                "exception": self._deployment_setup_data.get("exception")[1],
            }
        )
        self._plugin_manager.hook.boardfarm_release_devices(
            config=self.boardfarm_config,
            cmdline_args=self._session_config.option,
            plugin_manager=self._plugin_manager,
            deployment_status=deployment_status,
        )

    @pytest.hookimpl(hookwrapper=True)
    def pytest_sessionstart(self, session: Session) -> Generator[None, None, None]:
        """Deploy devices to environment and them release after use.

        :param session: pytest session instance
        :type session: Session
        """
        yield
        self._session_config = session.config
        self._plugin_manager.hook.boardfarm_configure(
            cmdline_args=self._session_config.option,
            plugin_manager=self._plugin_manager,
        )
        inventory_config = self._plugin_manager.hook.boardfarm_reserve_devices(
            cmdline_args=self._session_config.option,
            plugin_manager=self._plugin_manager,
        )
        self.boardfarm_config = parse_boardfarm_config(
            inventory_config, self._session_config.option.env_config
        )

    @staticmethod
    def _get_device_manager() -> Optional[DeviceManager]:
        try:
            return get_device_manager()
        except ValueError:
            return None

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtestloop(self, session: Session) -> Generator[None, None, None]:
        """Deploy devices to environment and them release after use.

        :param session: pytest session instance
        :type session: Session
        """
        logging_plugin: LoggingPlugin = session.config.pluginmanager.get_plugin(
            "logging-plugin"
        )
        device_manager = self._get_device_manager()
        try:
            if device_manager is None:
                logging_plugin.log_cli_handler.set_when("boardfarm setup")
                capture_boardfarm_logs(
                    logging_plugin,
                    self.deploy_boardfarm_devices,
                    capture_to=self._deployment_setup_data,
                )
            else:
                self.device_manager = device_manager
            yield
        finally:
            if device_manager is None:
                logging_plugin.log_cli_handler.set_when("boardfarm teardown")
                capture_boardfarm_logs(
                    logging_plugin,
                    self.release_boardfarm_devices,
                    capture_to=self._deployment_teardown_data,
                )

    @staticmethod
    def pytest_configure(config: Config) -> None:
        """Initialize env_req marker.

        :param config: pytest config
        :type config: Config
        """
        config.addinivalue_line(
            "markers",
            (
                "env_req(env_req: Dict): mark test with environment request. Skip"
                " test if environment check fails.\n"
                'Example: @pytest.mark.env_req({"environment_def":{"board":'
                '{"eRouter_Provisioning_mode":["dual"]}}})'
            ),
        )

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item: Item) -> Generator[None, None, None]:
        """Pytest run test setup hook wrapper to validate env_req marker.

        :param item: test item
        :type item: Item
        """
        env_req_marker = item.get_closest_marker("env_req")
        if (
            env_req_marker
            and env_req_marker.args
            and not is_env_matching(
                env_req_marker.args[0],
                self.boardfarm_config.env_config,
            )
        ):
            pytest.skip("Environment mismatch. Skipping")
        elif env_req_marker and env_req_marker.args:
            self._plugin_manager.hook.contingency_check(
                env_req=env_req_marker.args[0], device_manager=self.device_manager
            )

        yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self) -> Generator[None, None, None]:
        """Capture test start and end time for the html report."""
        self._test_start_time = datetime.now()
        yield
        self._test_start_time = None

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self) -> Generator[None, None, None]:
        """Save test start time to put in html execution report."""
        outcome = yield
        report: TestReport = outcome.get_result()  # type: ignore[attr-defined]
        report.test_start_time = self._test_start_time  # type: ignore[attr-defined]

    @staticmethod
    @pytest.hookimpl(optionalhook=True)
    def pytest_html_results_table_header(cells: list[Tag]) -> None:
        """Add test start time custom header in html report.

        :param cells: html table header list
        :type cells: list[Tag]
        """
        cells.insert(0, html.th("Start Time", class_="sortable time", col="time"))
        cells.insert(
            1,
            html.th(
                "Hidden Time",
                class_="sortable time",
                col="time",
                style="display: none;",
            ),
        )

    @staticmethod
    @pytest.hookimpl(optionalhook=True)
    def pytest_html_results_table_row(report: TestReport, cells: list[Tag]) -> None:
        """Add test test start time in the html report.

        :param report: test execution report
        :type report: TestReport
        :param cells: html table row list
        :type cells: list[Tag]
        """
        test_start_time = (
            report.test_start_time
            if hasattr(report, "test_start_time")
            else datetime.now()
        )
        epoch_time = test_start_time.strftime("%s %f")
        start_time_test = test_start_time.strftime("%d-%m-%Y %H:%M:%S:%f")
        cells.insert(0, html.td(epoch_time, class_="col-epoch", style="display: none;"))
        cells.insert(1, html.td(start_time_test, class_="col-time"))

    @pytest.hookimpl(optionalhook=True)
    def pytest_html_results_summary(self, postfix: list[Tag]) -> None:
        """Update the html report with boardfarm deployment and environment details.

        :param postfix: html report postfix content list
        :type postfix: list[Tag]
        """
        postfix.append(html.h3("Boardfarm"))
        postfix.append(
            get_boardfarm_html_table_report(
                self._session_config,
                self.device_manager,
                self.boardfarm_config,
                self._deployment_setup_data,
                self._deployment_teardown_data,
            )
        )
