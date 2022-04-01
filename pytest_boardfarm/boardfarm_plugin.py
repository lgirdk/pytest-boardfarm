"""pytest boardfarm plugin module."""
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Tuple

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import OptionGroup, Parser
from _pytest.logging import LoggingPlugin, _remove_ansi_escape_sequences, catching_logs
from _pytest.main import Session
from _pytest.nodes import Item
from _pytest.reports import TestReport
from boardfarm.devices.base_devices import BoardfarmDevice
from boardfarm.lib.boardfarm_config import BoardfarmConfig, parse_boardfarm_config
from boardfarm.lib.device_manager import DeviceManager
from boardfarm.main import get_plugin_manager
from py.xml import html  # pylint: disable=no-name-in-module,import-error

BOARDFARM_PLUGIN_NAME = "_boardfarm"


class _OptionGroup:
    """Argument parser option group."""

    # pylint: disable=too-few-public-methods

    def __init__(self, group: OptionGroup):
        """Initialize option group."""
        self._group = group

    def add_argument(self, *args: Tuple, **kwargs: Dict[str, Any]) -> None:
        """Add argument to option group."""
        self._group.addoption(*args, **kwargs)  # type: ignore


class _ArgumentParserWrapper:
    """Argument parser wrapper."""

    # pylint: disable=unused-argument

    def __init__(self, parser: Parser) -> None:
        """Initialize argument parser wrapper."""
        self._parser = parser
        self._group = parser.getgroup("boardfarm", "boardfarm")

    def add_argument_group(
        self, name: str, *args: Tuple, **kwargs: Dict[str, Any]
    ) -> _OptionGroup:
        """Add argument group to argument parser."""
        group_name = f"boardfarm-{name}"
        group = self._parser.getgroup(group_name, group_name)
        return _OptionGroup(group)

    def add_argument(self, *args: Tuple, **kwargs: Dict[str, Any]) -> None:
        """Add argument to argument parser."""
        self._group.addoption(*args, **kwargs)  # type: ignore


def is_env_matching(test_env_request: Any, boardfarm_env: Any) -> bool:
    """Check test environment request is a subset of boardfarm environment.

    Recursively checks dictionaries for match. A value of None in the test
    environment request is used as a wildcard, i.e. matches any values.
    A list in test environment request is considered as options in boardfarm
    environemt configuration.

    :param test_env_request: test environment request
    :param boardfarm_env: boardfarm environment data
    :return: True if test environment requirements are met, otherwise False
    """
    is_matching = False
    if test_env_request is None:
        is_matching = True
    elif (
        isinstance(test_env_request, dict)
        and isinstance(boardfarm_env, dict)
        and all(
            is_env_matching(v, boardfarm_env.get(k))
            for k, v in test_env_request.items()
        )
    ):
        is_matching = True
    elif (
        isinstance(test_env_request, list)
        and isinstance(boardfarm_env, (str, int, float, bool))
        and boardfarm_env in test_env_request
    ):
        is_matching = True
    elif (
        isinstance(boardfarm_env, list)
        and isinstance(test_env_request, (str, int, float, bool))
        and test_env_request in boardfarm_env
    ):
        is_matching = True
    elif (
        isinstance(test_env_request, dict)
        and isinstance(boardfarm_env, list)
        and any(is_env_matching(test_env_request, item) for item in boardfarm_env)
    ):
        is_matching = True
    elif (
        isinstance(test_env_request, list)
        and isinstance(boardfarm_env, list)
        and all(is_env_matching(item, boardfarm_env) for item in test_env_request)
    ):
        is_matching = True
    elif (
        isinstance(test_env_request, list)
        and isinstance(boardfarm_env, dict)
        and any(is_env_matching(item, boardfarm_env) for item in test_env_request)
    ):
        is_matching = True
    elif test_env_request == boardfarm_env:
        is_matching = True
    return is_matching


class BoardfarmPlugin:
    """Pytest boardfarm plugin."""

    # pylint: disable=no-member  # hook calls are not a member

    def __init__(self) -> None:
        """Initialize boardfarm plugin."""
        self._session_config: Config = None
        self._test_start_time: datetime = None
        self._deployment_setup_data: Dict = {}
        self._deployment_teardown_data: Dict = {}
        self._plugin_manager = get_plugin_manager()
        self.device_manager: DeviceManager = None
        self.boardfarm_config: BoardfarmConfig = None

    def pytest_addoption(self, parser: Parser) -> None:
        """Add command line arguments to pytest.

        :param parser: argument parser
        """
        self._plugin_manager.hook.boardfarm_add_cmdline_args(
            argparser=_ArgumentParserWrapper(parser)
        )

    def deploy_boardfarm_devices(self) -> None:
        """Deploy boardfarm devices to the environment."""
        self.boardfarm_config = parse_boardfarm_config(
            self._session_config.option.board_name,
            self._session_config.option.env_config,
            self._session_config.option.inventory_config,
        )
        self._plugin_manager.hook.boardfarm_configure(
            config=self.boardfarm_config,
            cmdline_args=self._session_config.option,
            plugin_manager=self._plugin_manager,
        )
        self._plugin_manager.hook.boardfarm_reserve_devices(
            config=self.boardfarm_config,
            cmdline_args=self._session_config.option,
            plugin_manager=self._plugin_manager,
        )
        self.device_manager = self._plugin_manager.hook.boardfarm_deploy_devices(
            config=self.boardfarm_config,
            cmdline_args=self._session_config.option,
            plugin_manager=self._plugin_manager,
        )

    def release_boardfarm_devices(self) -> None:
        """Release boardfarm devices after the test execution."""
        self._plugin_manager.hook.boardfarm_release_devices(
            config=self.boardfarm_config,
            cmdline_args=self._session_config.option,
            plugin_manager=self._plugin_manager,
        )

    @staticmethod
    def _capture_boardfarm_logs(
        logging_plugin: LoggingPlugin, function: Callable, capture_to: Dict
    ) -> None:
        """Capture boardfarm logs on given function execution.

        This mothod captures the logs to given 'capture_to' dictionary argument.
        Both logs and exceptions are captured to the dictionary with keys 'logs' and
        'exception'. These values will be used for html report generation.

        :param logging_plugin: pytest logging plugin
        :param function: function that requires log capture
        :param capture_to: dictionary instance to save captured logs
        """
        with catching_logs(
            logging_plugin.report_handler, logging_plugin.log_level
        ) as report_logger:
            report_logger.reset()
            try:
                function()
            except:  # noqa: E722,B001 # we capture all exceptions
                capture_to["exception"] = sys.exc_info()
                raise
            finally:
                capture_to["logs"] = _remove_ansi_escape_sequences(
                    report_logger.stream.getvalue().strip()
                )
                report_logger.reset()

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtestloop(self, session: Session) -> Generator:
        """Deploy devices to environment and them release after use.

        :param session: pytest session instance
        """
        self._session_config = session.config
        logging_plugin: LoggingPlugin = session.config.pluginmanager.get_plugin(
            "logging-plugin"
        )
        try:
            logging_plugin.log_cli_handler.set_when("boardfarm setup")
            self._capture_boardfarm_logs(
                logging_plugin,
                self.deploy_boardfarm_devices,
                capture_to=self._deployment_setup_data,
            )
            yield
        finally:
            logging_plugin.log_cli_handler.set_when("boardfarm teardown")
            self._capture_boardfarm_logs(
                logging_plugin,
                self.release_boardfarm_devices,
                capture_to=self._deployment_teardown_data,
            )

    @staticmethod
    def pytest_configure(config: Config) -> None:
        """Initialize env_req marker.

        :param config: pytest config
        """
        config.addinivalue_line(
            "markers",
            "env_req(env_req: Dict): mark test with environment request. Skip"
            " test if environment check fails.\n"
            'Example: @pytest.mark.env_req({"environment_def":{"board":'
            '{"eRouter_Provisioning_mode":["dual"]}}})',
        )

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_setup(self, item: Item) -> Generator:
        """Pytest run test setup hook wrapper to validate env_req marker.

        :param item: test item
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
        yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self) -> Generator:
        """Capture test start and end time for the html report."""
        self._test_start_time = datetime.now()
        yield
        self._test_start_time = None

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self) -> Generator:
        """Save test start time to put in html execution report."""
        outcome = yield
        report: TestReport = outcome.get_result()
        report.test_start_time = self._test_start_time  # type: ignore[attr-defined]

    @staticmethod
    @pytest.hookimpl(optionalhook=True)
    def pytest_html_results_table_header(cells: List) -> None:
        """Add test start time custom header in html report.

        :param cells: html table header list
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
    def pytest_html_results_table_row(report: TestReport, cells: List) -> None:
        """Add test test start time in the html report.

        :param report: test execution report
        :param cells: html table row list
        """
        epoch_time = report.test_start_time.strftime("%s %f")
        start_time_test = report.test_start_time.strftime("%d-%m-%Y %H:%M:%S:%f")
        cells.insert(0, html.td(epoch_time, class_="col-epoch", style="display: none;"))
        cells.insert(1, html.td(start_time_test, class_="col-time"))

    def _get_value_from_dict(self, key: str, dictionary: Dict) -> Any:
        """Get value of given key from the dictionary recursively.

        This method is used to avoid nested checks for None value to get
        a value which is in a dictionary without raising a KeyError.

        :param key: key name
        :param dictionary: dictionary instance
        :return: value of given key if exists, otherwise None
        """
        for name, value in dictionary.items():
            if name == key:
                return value
            if isinstance(value, dict):
                return_value = self._get_value_from_dict(key, value)
                if return_value is not None:
                    return return_value
        return None

    def _get_boardfarm_environment_details(self) -> Dict:
        """Get boardfarm environment details for html report.

        :return: boardfarm environment details dictionary
        """
        boardfarm_env_details = {
            "Board name": self._session_config.option.board_name,
            "Image name": self._get_value_from_dict(
                "image_uri", self.boardfarm_config.env_config
            ),
            "Provision mode": self._get_value_from_dict(
                "eRouter_Provisioning_mode", self.boardfarm_config.env_config
            ),
            "Inventory config": Path(
                self._session_config.option.inventory_config
            ).resolve(),
            "Environment config": Path(
                self._session_config.option.env_config
            ).resolve(),
        }
        return boardfarm_env_details

    @staticmethod
    def _get_onclick_javascript(button_id: str, logs_id: str) -> str:
        """Get onclick javascript to show and hide deployment logs.

        :param button_id: button html component id
        :param logs_id: logs html component id
        :return: javascript to toggle logs on click
        """
        return (
            f"var el = getElementById('{logs_id}'); "
            "if (el.style.display=='none') { "
            "  el.style.display=''; "
            f"  getElementById('{button_id}').innerHTML='hide logs'"
            "} else {"
            "  el.style.display='none'; "
            f"  getElementById('{button_id}').innerHTML='view logs'"
            "}"
        )

    def _get_boardfarm_deployment_status(self, stage: str, stage_logs: Dict) -> List:
        """Get boardfarm deployment status html table content.

        :param stage: deployment stage name
        :param stage_logs: captured deployment logs
        :return: html table row's with given deployment stage status
        """
        console_logs = stage_logs.get("logs", "")
        if "exception" in stage_logs:
            deployment_stage_css_style = "color: red;"
            deployment_stage_status = f"Failed - {repr(stage_logs['exception'][1])}"
            console_logs += "".join(traceback.format_tb(stage_logs["exception"][2]))
        else:
            deployment_stage_status = "Success"
            deployment_stage_css_style = "color: green;"
        td_css_style = "border: 1px solid #E6E6E6; padding: 3px;"
        return [
            html.tr(
                html.td(f"Boardfarm {stage}", style=td_css_style),
                html.td(
                    deployment_stage_status,
                    html.span(
                        "hide logs" if "exception" in stage_logs else "view logs",
                        id=f"boardfarm-{stage}-button",
                        onclick=self._get_onclick_javascript(
                            f"boardfarm-{stage}-button", f"boardfarm-{stage}-logs"
                        ),
                        style="font-style:oblique;padding-left:5px;color:#1A237E;",
                    ),
                    style=f"{td_css_style}{deployment_stage_css_style}",
                ),
            ),
            html.tr(
                html.td(html.div(console_logs, class_="log"), colspan="2"),
                id=f"boardfarm-{stage}-logs",
                style="" if "exception" in stage_logs else "display: none;",
            ),
        ]

    @pytest.hookimpl(optionalhook=True)
    def pytest_html_results_summary(self, postfix: List) -> None:
        """Update the html report with boardfarm deployment and environment details.

        :param postfix: html report postfix content list
        """
        td_style = "padding: 3px; border: 1px solid #E6E6E6;"
        table_contents = [
            html.tr(html.td(title, style=td_style), html.td(content, style=td_style))
            for title, content in self._get_boardfarm_environment_details().items()
        ]
        table_contents.extend(
            self._get_boardfarm_deployment_status("setup", self._deployment_setup_data)
        )
        table_contents.extend(
            self._get_boardfarm_deployment_status(
                "teardown", self._deployment_teardown_data
            )
        )
        if self.device_manager is not None:
            deployed_devices = {
                name: device.device_type
                for name, device in self.device_manager.get_devices_by_type(
                    BoardfarmDevice
                ).items()
            }
            table_contents.append(
                html.tr(
                    html.td("Deployed devices", style=td_style),
                    html.td(json.dumps(deployed_devices), style=td_style),
                )
            )
        postfix.append(html.h3("Boardfarm"))
        postfix.append(html.table([html.tbody(table_contents)]))
