"""Pytest execution html report."""
import json
import traceback
from pathlib import Path
from typing import Any, Dict, List

from _pytest.config import Config
from boardfarm3.devices.base_devices import BoardfarmDevice
from boardfarm3.lib.boardfarm_config import BoardfarmConfig
from boardfarm3.lib.device_manager import DeviceManager
from py.xml import Tag, html  # pylint: disable=no-name-in-module,import-error

_TD_CSS_STYLE = "border: 1px solid #E6E6E6; padding: 3px;"
_BUTTON_CSS_STYLE = (
    "font-style: oblique; padding-left: 5px; color: #1A237E; cursor: pointer;"
)


def _get_value_from_dict(key: str, dictionary: Dict) -> Any:
    """Get value of given key from the dictionary recursively.

    This method is used to avoid nested checks for None to get
    a value from dictionary without raising KeyError.

    :param key: key name
    :param dictionary: dictionary instance
    :return: value of given key if exists, otherwise None
    """
    for name, value in dictionary.items():
        if name == key:
            return value
        if isinstance(value, dict):
            return_value = _get_value_from_dict(key, value)
            if return_value is not None:
                return return_value
    return None


def _get_boardfarm_environment_details(
    session_config: Config, boardfarm_config: BoardfarmConfig
) -> Dict:
    """Get boardfarm environment details for html report.

    :param session_config: pytest session config
    :param boardfarm_config: boardfarm config
    :return: boardfarm environment details dictionary
    """
    boardfarm_env_details = {
        "Board name": session_config.option.board_name,
        "Image name": _get_value_from_dict("image_uri", boardfarm_config.env_config),
        "Provision mode": _get_value_from_dict(
            "eRouter_Provisioning_mode", boardfarm_config.env_config
        ),
    }
    return boardfarm_env_details


def _get_onclick_javascript(button_id: str, content_id: str, content_type: str) -> str:
    """Get onclick javascript to show and hide deployment logs.

    :param button_id: html button element id
    :param content_id: html content element id
    :param content_type: type of the html content
    :return: javascript to toggle logs on click
    """
    return (
        f"var el = getElementById('{content_id}'); "
        "if (el.style.display=='none') { "
        "  el.style.display=''; "
        f"  getElementById('{button_id}').innerHTML='hide {content_type}'"
        "} else {"
        "  el.style.display='none'; "
        f"  getElementById('{button_id}').innerHTML='view {content_type}'"
        "}"
    )


def _get_boardfarm_deployment_status(stage: str, stage_logs: Dict) -> List:
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
    return [
        html.tr(
            html.td(f"Boardfarm {stage}", style=_TD_CSS_STYLE),
            html.td(
                deployment_stage_status,
                html.span(
                    "hide logs" if "exception" in stage_logs else "view logs",
                    id=f"boardfarm-{stage}-button",
                    onclick=_get_onclick_javascript(
                        f"boardfarm-{stage}-button",
                        f"boardfarm-{stage}-logs",
                        "logs",
                    ),
                    style=_BUTTON_CSS_STYLE,
                ),
                style=f"{_TD_CSS_STYLE}{deployment_stage_css_style}",
            ),
        ),
        html.tr(
            html.td(
                html.div(console_logs, class_="log", style="word-break: break-all;"),
                colspan="2",
            ),
            id=f"boardfarm-{stage}-logs",
            style="" if "exception" in stage_logs else "display: none;",
        ),
    ]


def _get_boardfarm_config_table_data(
    config_name: str, config_path: str, json_config: str
) -> List:
    """Get boardfarm config details to put in pytest html report.

    :param config_name: config name
    :param config_path: config file path
    :param json_config: formatted json config
    :return: html table row's with given config details
    """
    return [
        html.tr(
            html.td(f"{config_name.capitalize()} config", style=_TD_CSS_STYLE),
            html.td(
                config_path,
                html.span(
                    "view config",
                    id=f"boardfarm-{config_name}-button",
                    onclick=_get_onclick_javascript(
                        f"boardfarm-{config_name}-button",
                        f"boardfarm-{config_name}-config",
                        "config",
                    ),
                    style=_BUTTON_CSS_STYLE,
                ),
                style=_TD_CSS_STYLE,
            ),
        ),
        html.tr(
            html.td(
                html.div(json_config, class_="log", style="word-break: break-all;"),
                colspan="2",
            ),
            id=f"boardfarm-{config_name}-config",
            style="display: none;",
        ),
    ]


def _get_boardfarm_configs_details(session_config: Config) -> List:
    """Get boardfarm config details as html table rows.

    :param session_config: pytest session config
    :return: html table rows with boardfarm config details
    """
    environment_config_path = Path(session_config.option.env_config)
    inventory_config_path = Path(session_config.option.inventory_config)
    full_inventory_config = json.loads(
        inventory_config_path.read_text(encoding="utf-8")
    )
    board_name = session_config.option.board_name
    if board_name in full_inventory_config:
        inventory_config_json = {
            board_name: full_inventory_config.get(board_name),
            full_inventory_config.get(board_name)[
                "location"
            ]: full_inventory_config.get(
                full_inventory_config.get(board_name)["location"]
            ),
        }
    else:
        inventory_config_json = full_inventory_config
    config_details = _get_boardfarm_config_table_data(
        "inventory",
        str(inventory_config_path.resolve()),
        json.dumps(inventory_config_json, indent=2),
    )
    config_details.extend(
        _get_boardfarm_config_table_data(
            "environment",
            str(environment_config_path.resolve()),
            json.dumps(
                json.loads(environment_config_path.read_text(encoding="utf-8")),
                indent=2,
            ),
        )
    )
    return config_details


def get_boardfarm_html_table_report(
    session_config: Config,
    device_manager: DeviceManager,
    boardfarm_config: BoardfarmConfig,
    deployment_setup_data: Dict,
    deployment_teardown_data: Dict,
) -> Tag:
    """Get boardfarm html table report.

    :param session_config: pytest session config
    :param device_manager: boardfarm device manager
    :param boardfarm_config: boardfarm config
    :param deployment_setup_data: boardfarm deployment status data
    :param deployment_teardown_data: boardfarm deployment teardown data
    :return: boardfarm html table report
    """
    table_contents = [
        html.tr(
            html.td(title, style=_TD_CSS_STYLE),
            html.td(content, style=_TD_CSS_STYLE),
        )
        for title, content in _get_boardfarm_environment_details(
            session_config, boardfarm_config
        ).items()
    ]
    table_contents.extend(_get_boardfarm_configs_details(session_config))
    table_contents.extend(
        _get_boardfarm_deployment_status("setup", deployment_setup_data)
    )
    table_contents.extend(
        _get_boardfarm_deployment_status("teardown", deployment_teardown_data)
    )
    if device_manager is not None:
        deployed_devices = {
            name: device.device_type
            for name, device in device_manager.get_devices_by_type(
                BoardfarmDevice
            ).items()
        }
        table_contents.append(
            html.tr(
                html.td("Deployed devices", style=_TD_CSS_STYLE),
                html.td(json.dumps(deployed_devices), style=_TD_CSS_STYLE),
            )
        )
    return html.table(html.tbody(table_contents))
