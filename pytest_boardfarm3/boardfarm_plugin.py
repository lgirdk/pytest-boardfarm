"""pytest boardfarm plugin module."""

from __future__ import annotations

import asyncio
import base64
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from boardfarm3.lib.boardfarm_config import BoardfarmConfig, parse_boardfarm_config
from boardfarm3.lib.device_manager import DeviceManager, get_device_manager
from boardfarm3.main import get_plugin_manager
from pytest import CallInfo, Config, Item, Parser, Session, TestReport  # noqa: PT013

from pytest_boardfarm3.lib.argument_parser import ArgumentParser
from pytest_boardfarm3.lib.html_report import get_boardfarm_html_table_report
from pytest_boardfarm3.lib.utils import capture_boardfarm_logs, is_env_matching

if TYPE_CHECKING:
    from collections.abc import Generator

    from _pytest.config import _PluggyPlugin
    from _pytest.logging import LoggingPlugin


BOARDFARM_PLUGIN_NAME = "_boardfarm"


THIS_TZ = datetime.now(timezone.utc).astimezone().tzinfo


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
            argparser=ArgumentParser(parser),
        )

    def deploy_boardfarm_devices(self) -> None:
        """Deploy boardfarm devices to the environment."""
        self.device_manager = self._plugin_manager.hook.boardfarm_register_devices(
            config=self.boardfarm_config,
            cmdline_args=self._session_config.option,
            plugin_manager=self._plugin_manager,
        )
        asyncio.run(
            self._plugin_manager.hook.boardfarm_setup_env(
                config=self.boardfarm_config,
                cmdline_args=self._session_config.option,
                plugin_manager=self._plugin_manager,
                device_manager=self.device_manager,
            ),
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
            inventory_config,
            self._session_config.option.env_config,
        )

    @staticmethod
    def _get_device_manager() -> DeviceManager | None:
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
            "logging-plugin",
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
            "env_req(env_req: Dict): mark test with environment request. Skip"
            " test if environment check fails.\n"
            'Example: @pytest.mark.env_req({"environment_def":{"board":'
            '{"eRouter_Provisioning_mode":["dual"]}}})',
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
                env_req=env_req_marker.args[0],
                device_manager=self.device_manager,
            )

        yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self) -> Generator[None, None, None]:
        """Capture test start and end time for the html report."""
        self._test_start_time = datetime.now(tz=THIS_TZ)
        yield
        self._test_start_time = None

    def _image_to_base64(self, image_path: str) -> str:
        with Path(image_path).open("rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def _add_screenshots_to_pytest_html(
        self, report: TestReport, pytest_html: _PluggyPlugin
    ) -> None:
        """Add screenshots to pytest html report."""
        extras: list[Any] = getattr(report, "extras", [])
        if "screenshot" in report.caplog.lower():
            screenshot_paths = re.findall(r"'([^']*.png)'", report.caplog)
            if report.when == "call":
                extras = [
                    pytest_html.extras.image(  # type: ignore[attr-defined]
                        self._image_to_base64(screenshot_path)
                    )
                    for screenshot_path in screenshot_paths
                ]
                report.extras = extras  # type: ignore[attr-defined]

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(
        self,
        item: Item,
        call: CallInfo,  # noqa: ARG002
    ) -> Generator[None, None, None]:
        """Save test start time to put in html execution report."""
        pytest_html = item.config.pluginmanager.getplugin("html")
        outcome = yield
        report: TestReport = outcome.get_result()  # type: ignore[attr-defined]
        report.test_start_time = self._test_start_time  # type: ignore[attr-defined]
        self._add_screenshots_to_pytest_html(report, pytest_html)

    @staticmethod
    @pytest.hookimpl(optionalhook=True)
    def pytest_html_results_table_header(cells: list[str]) -> None:
        """Add test start time custom header in html report.

        :param cells: html table header list
        :type cells: list[str]
        """
        cells.insert(0, '<th class="sortable" data-column-type="time">Start Time</th>')
        cells.insert(
            1,
            '<th class="sortable" data-column-type="time" style="display: none;">'
            "Hidden Time</th>",
        )

    @staticmethod
    @pytest.hookimpl(optionalhook=True)
    def pytest_html_results_table_row(report: TestReport, cells: list[str]) -> None:
        """Add test test start time in the html report.

        :param report: test execution report
        :type report: TestReport
        :param cells: html table row list
        :type cells: list[str]
        """
        test_start_time = (
            report.test_start_time
            if hasattr(report, "test_start_time")
            else datetime.now(tz=THIS_TZ)
        )
        epoch_time = test_start_time.strftime("%s %f")
        start_time_test = test_start_time.strftime("%d-%m-%Y %H:%M:%S:%f")
        cells.insert(
            0,
            f'<td class="col-time" style="display: none;">{epoch_time}</td>',
        )
        cells.insert(1, f'<td class="col-time">{start_time_test}</td>')

    @pytest.hookimpl(optionalhook=True)
    def pytest_html_results_summary(self, postfix: list[str]) -> None:
        """Update the html report with boardfarm deployment and environment details.

        :param postfix: html report postfix content list
        :type postfix: list[str]
        """
        postfix.extend(
            [
                "<h3>Boardfarm</h3>",
                get_boardfarm_html_table_report(
                    self._session_config,
                    self.device_manager,
                    self.boardfarm_config,
                    self._deployment_setup_data,
                    self._deployment_teardown_data,
                ),
                "<br>",
            ],
        )
