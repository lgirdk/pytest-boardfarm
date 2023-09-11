"""Pytest execution html report."""
import json
import traceback
from pathlib import Path

from boardfarm3.devices.base_devices import BoardfarmDevice
from boardfarm3.lib.boardfarm_config import BoardfarmConfig
from boardfarm3.lib.device_manager import DeviceManager
from boardfarm3.lib.utils import get_value_from_dict
from pytest import Config  # noqa: PT013

_TD_CSS_STYLE = "border: 1px solid #E6E6E6; padding: 3px;"
_BUTTON_CSS_STYLE = (
    "font-style: oblique; padding-left: 5px; color: #1A237E; cursor: pointer;"
)


def _get_boardfarm_environment_details(
    session_config: Config,
    boardfarm_config: BoardfarmConfig,
) -> dict[str, str]:
    """Get boardfarm environment details for html report.

    :param session_config: pytest session config
    :type session_config: Config
    :param boardfarm_config: boardfarm config
    :type boardfarm_config: BoardfarmConfig
    :return: boardfarm environment details dictionary
    :rtype: dict[str, str]
    """
    return {
        "Board name": session_config.option.board_name,
        "Image name": get_value_from_dict("image_uri", boardfarm_config.env_config),
        "Provision mode": get_value_from_dict(
            "eRouter_Provisioning_mode",
            boardfarm_config.env_config,
        ),
    }


def _get_onclick_javascript(button_id: str, content_id: str, content_type: str) -> str:
    """Get onclick javascript to show and hide deployment logs.

    :param button_id: html button element id
    :type button_id: str
    :param content_id: html content element id
    :type content_id: str
    :param content_type: type of the html content
    :type content_type: str
    :return: javascript to toggle logs on click
    :rtype: str
    """
    return (
        f"var el = getElementById({content_id!r}); "
        "if (el.style.display=='none') { "
        "  el.style.display=''; "
        f"  getElementById({button_id!r}).innerHTML='hide {content_type}'"
        "} else {"
        "  el.style.display='none'; "
        f"  getElementById({button_id!r}).innerHTML='view {content_type}'"
        "}"
    )


def _get_boardfarm_deployment_status(stage: str, stage_logs: dict) -> list[str]:
    """Get boardfarm deployment status html table content.

    :param stage: deployment stage name
    :type stage: str
    :param stage_logs: captured deployment logs
    :type stage_logs: dict
    :return: html table row's with given deployment stage status
    :rtype: list[str]
    """
    console_logs = stage_logs.get("logs", "")
    if "exception" in stage_logs:
        logs_toggle_button = "hide logs"
        deployment_stage_css_style = "color: red;"
        deployment_stage_status = f"Failed - {stage_logs['exception'][1]!r}"
        console_logs += "".join(traceback.format_tb(stage_logs["exception"][2]))
    else:
        logs_toggle_button = "view logs"
        deployment_stage_status = "Success"
        deployment_stage_css_style = "color: green;"
    span_onclick = _get_onclick_javascript(
        f"boardfarm-{stage}-button",
        f"boardfarm-{stage}-logs",
        "logs",
    )
    span = (
        f'<span style="{_BUTTON_CSS_STYLE}" id="boardfarm-{stage}-button"'
        f' onclick="{span_onclick}" >{logs_toggle_button}</span>'
    )
    logs_style = "" if "exception" in stage_logs else "display: none;"
    return [
        (
            f'<tr><td style="{_TD_CSS_STYLE}">Boardfarm {stage}</td><td'
            f' style="{_TD_CSS_STYLE} {deployment_stage_css_style}">'
            f"{deployment_stage_status} {span}</td></tr>"
        ),
        (
            f'<tr id="boardfarm-{stage}-logs" style="{logs_style}"><td colspan="2"><div'
            ' class="logwrapper" style="max-height: none"><div class="log"'
            ' style="word-break: break-all; top: 0px;"'
            f">{console_logs}</div></div></td></tr>"
        ),
    ]


def _get_boardfarm_config_table_data(
    config_name: str,
    config_path: str,
    json_config: str,
) -> list[str]:
    """Get boardfarm config details to put in pytest html report.

    :param config_name: config name
    :type config_name: str
    :param config_path: config file path
    :type config_path: str
    :param json_config: formatted json config
    :type json_config: str
    :return: html table row's with given config details
    :rtype: list[str]
    """
    span_onclick = _get_onclick_javascript(
        f"boardfarm-{config_name}-button",
        f"boardfarm-{config_name}-config",
        "config",
    )
    span = (
        f'<span style="{_BUTTON_CSS_STYLE}" id="boardfarm-{config_name}-button"'
        f' onclick="{span_onclick}">view config</span>'
    )
    return [
        (
            f'<r><td style="{_TD_CSS_STYLE}">{config_name.capitalize()} config</td><td'
            f' style="{_TD_CSS_STYLE}">{config_path} {span}</td></tr>'
        ),
        (
            f'<tr id="boardfarm-{config_name}-config" style="display: none;"><td'
            ' colspan="2"><div class="logwrapper" style="max-height: none"><div'
            ' class="log"style="word-break: break-all; top: 0px;"'
            f">{json_config}</div></div></td></tr>"
        ),
    ]


def _get_boardfarm_configs_details(
    session_config: Config,
    boardfarm_config: BoardfarmConfig,
) -> list[str]:
    """Get boardfarm config details as html table rows.

    :param session_config: pytest session config
    :type session_config: Config
    :param boardfarm_config: boardfarm config
    :type boardfarm_config: BoardfarmConfig
    :return: html table rows with boardfarm config details
    :rtype: list[str]
    """
    environment_config_path = Path(session_config.option.env_config)
    inventory_config_path = Path(session_config.option.inventory_config)
    config_details = _get_boardfarm_config_table_data(
        "inventory",
        str(inventory_config_path),
        json.dumps(boardfarm_config.inventory_config, indent=2),
    )
    config_details.extend(
        _get_boardfarm_config_table_data(
            "environment",
            str(environment_config_path),
            json.dumps(boardfarm_config.env_config, indent=2),
        ),
    )
    return config_details


def get_boardfarm_html_table_report(
    session_config: Config,
    device_manager: DeviceManager,
    boardfarm_config: BoardfarmConfig,
    deployment_setup_data: dict,
    deployment_teardown_data: dict,
) -> str:
    """Get boardfarm html table report.

    :param session_config: pytest session config
    :type session_config: Config
    :param device_manager: boardfarm device manager
    :type device_manager: DeviceManager
    :param boardfarm_config: boardfarm config
    :type boardfarm_config: BoardfarmConfig
    :param deployment_setup_data: boardfarm deployment status data
    :type deployment_setup_data: dict
    :param deployment_teardown_data: boardfarm deployment teardown data
    :type deployment_teardown_data: dict
    :return: boardfarm html table report
    :rtype: str
    """
    table_contents = [
        f'<tr><td style="{_TD_CSS_STYLE}">{title}</td><td'
        f' style="{_TD_CSS_STYLE}">{content}</td></tr>'
        for title, content in _get_boardfarm_environment_details(
            session_config,
            boardfarm_config,
        ).items()
    ]
    table_contents.extend(
        _get_boardfarm_configs_details(session_config, boardfarm_config),
    )
    if deployment_setup_data:
        table_contents.extend(
            _get_boardfarm_deployment_status("setup", deployment_setup_data),
        )
    if deployment_teardown_data:
        table_contents.extend(
            _get_boardfarm_deployment_status("teardown", deployment_teardown_data),
        )
    if device_manager is not None:
        deployed_devices = {
            name: device.device_type
            for name, device in device_manager.get_devices_by_type(
                BoardfarmDevice,
            ).items()
        }
        table_contents.append(
            f'<tr><td style="{_TD_CSS_STYLE}">Deployed devices</td><td'
            f' style="{_TD_CSS_STYLE}">{json.dumps(deployed_devices)}</td></tr>',
        )
    return f'<table><tbody>{"".join(table_contents)}</tbody></table>'
