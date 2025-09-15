# Pytest Boardfarm

<p align="center">
  <img src="https://raw.githubusercontent.com/lgirdk/pytest-boardfarm/boardfarm3/images/BoardFarm.png" width="350"/><br>
  <img alt="GitHub commit activity (branch)"
       src="https://img.shields.io/github/commit-activity/t/lgirdk/pytest-boardfarm/boardfarm3">
  <img alt="GitHub last commit (branch)"
       src="https://img.shields.io/github/last-commit/lgirdk/pytest-boardfarm/boardfarm3">
  <img alt="Python Version" src="https://img.shields.io/badge/python-3.11+-blue">
  <a href="https://github.com/psf/black"><img alt="Code style: black"
       src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
  <a href="https://github.com/astral-sh/ruff"><img alt="Lint: ruff"
       src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json"></a>
</p>
<hr>

`pytest-boardfarm3` is the extension that integrates Boardfarm with Pytest.
It adapts Boardfarm's plugin/runner lifecycle into Pytest sessions and exposes convenient fixtures for tests and interactive sessions.

> **Prerequisites**
>
> - Boardfarm must be installed and available on the Python path (the plugin expects boardfarm3 APIs).
> - Python 3.11+ is recommended (Boardfarm uses modern Python features).
> - Pytest (and optionally pytest-html if you want HTML reports).

---

## Table of contents

- [Overview](https://github.com/lgirdk/pytest-boardfarm/blob/boardfarm3/README.md#overview)
- [Quick install](https://github.com/lgirdk/pytest-boardfarm/blob/boardfarm3/README.md#quick-install)
- [How the plugin loads](https://github.com/lgirdk/pytest-boardfarm/blob/boardfarm3/README.md#how-the-plugin-loads)
- [Command-line options and selection](https://github.com/lgirdk/pytest-boardfarm/blob/boardfarm3/README.md#command-line-options-and-selection)
- [Fixtures provided](https://github.com/lgirdk/pytest-boardfarm/blob/boardfarm3/README.md#fixtures-provided)
- [Markers](https://github.com/lgirdk/pytest-boardfarm/blob/boardfarm3/README.md#markers)
- [Running tests — examples](https://github.com/lgirdk/pytest-boardfarm/blob/boardfarm3/README.md#running-tests--examples)
- [How the plugin orchestrates Boardfarm](https://github.com/lgirdk/pytest-boardfarm/blob/boardfarm3/README.md#how-the-plugin-orchestrates-boardfarm)
- [HTML report integration](https://github.com/lgirdk/pytest-boardfarm/blob/boardfarm3/README.md#html-report-integration)
- [Troubleshooting & tips](https://github.com/lgirdk/pytest-boardfarm/blob/boardfarm3/README.md#troubleshooting--tips)
- [Development notes](https://github.com/lgirdk/pytest-boardfarm/blob/boardfarm3/README.md#development-notes)
- [License](https://github.com/lgirdk/pytest-boardfarm/blob/boardfarm3/README.md#license)

---

## Overview

`pytest-boardfarm` is responsible for the following operations:

- Registers Boardfarm `fixtures` and a `BoardfarmPlugin` object that coordinates environment parsing, device registration, deployment and teardown.
- Exposes device_manager, boardfarm_config, bf_context and bf_logger fixtures to tests.
- Orchestrates a multi-phase boot/config lifecycle via Boardfarm pluggy hooks when pytest runs (deploys devices before tests and releases them at the end).
- Adds a small test selector (`--test-names`) to limit which tests are executed by name.
- Integrates with pytest-html to add Boardfarm deployment metadata and captured images to generated HTML reports.

---

## Quick install

```bash
pip install "boardfarm3[pytest]"
```

### Development Install

Install Boardfarm and the pytest plugin.
If the plugin is packaged locally, install it in editable mode for development.

```bash
git clone http://github.com/lgirdk/pytest-boardfarm
cd pytest-boardfarm
pip install -e .     # if plugin packaged locally with proper entry-point
```

The plugin package should expose the pytest entry point so pytest can auto-discover it. **Ensure boardfarm is also installed in the same environment.**

## How the plugin loads

There are two important registration points in the plugin code:

1. An early conftest hook registers a minimal fixtures module so small utilities are available early (`bf_context`, `bf_logger`). The heavier `BoardfarmPlugin` instance is registered conditionally based on detected command-line args.

2. The `BoardfarmPlugin` class is the main integration surface. It adds CLI args via `boardfarm_add_cmdline_args`, parses inventory and env JSONs, registers and sets up devices through Boardfarm pluggy hooks, and performs teardown and release at session end.

This separation allows lightweight test runs to use a couple of fixtures without provisioning devices, and it enables full Boardfarm provisioning only when requested.

## Command-line options and selection

The plugin adds a test selection option named `--test-names` which accepts a space-separated list of logical test names. When provided, collected tests are filtered: only items matching normalized `test_<name>`.

Boardfarm's own CLI options (for example: `board-name`, `env-config`, `inventory-config`, `skip-boot`, `skip-contingency-checks`, `save-console-logs`) are exposed by the plugin through the `BoardfarmPlugin` lifecycle. Once the plugin is active you can inspect available options using pytest's help output.

```bash
$ pytest -h
usage: pytest [options] [file_or_dir] [file_or_dir] [...]

...
boardfarm:
  --board-name=BOARD_NAME
                        Board name
  --env-config=ENV_CONFIG
                        Environment JSON config file path
  --inventory-config=INVENTORY_CONFIG
                        Inventory JSON config file path
  --legacy              allows for devices.<device> obj to be exposed (only for legacy use)
  --skip-boot           Skips the booting process, all devices will be used as they are
  --skip-contingency-checks
                        Skip contingency checks while running tests
  --save-console-logs=SAVE_CONSOLE_LOGS
                        Save the console logs at the give location
  --ignore-devices=IGNORE_DEVICES
                        Ignore the given devices (names are comma separated). Useful when a device is incommunicado

Custom options:
  --test-names=TEST_NAMES
                        Test names for which the execution will be performed
```

---

## Fixtures provided

The plugin exposes several fixtures aimed at easing device interaction, configuration access and contextual logging. Most of these are session scoped.

- `bf_context` (function scope): Returns a `ContextStorage` instance useful for sharing ephemeral data within a single test.

    ```python
    def test_example(bf_context):
        bf_context['foo'] = 'bar'
    ```

- `bf_logger` (session autouse): Returns a `TestLogger` instance for step-level logging and tracing.

    ```python
    def test_log(bf_logger):
        bf_logger.step("Connect to DUT")
    ```

- `boardfarm_config` (session): Returns the resolved `BoardfarmConfig` that the plugin created by merging inventory, env files and CLI overrides. Use this to inspect provisioning mode and environment definitions.

    ```python
    def test_config(boardfarm_config):
        assert boardfarm_config.get_prov_mode() in ("ipv4","ipv6","dual")
    ```

- `device_manager` (session): Returns the `DeviceManager` that holds instantiated device objects constructed from the inventory. Use it to query devices by template/interface or type.

    ```python
    def test_device(device_manager):
        cpe = device_manager.get_device_by_type(CPE)
        assert cpe is not None
    ```

These fixtures are intended to be the main integration points for tests and interactive sessions.

> **Important**: Tests should call use-cases and obtain devices through `device_manager` rather than instantiating devices directly.

## Markers

### `@pytest.mark.env_req(...)`

`env_req` is a custom marker introduced by the plugin to declare an environment requirement for the test. If the current Boardfarm environment does not satisfy the requested env_req, the test will be skipped.

**Example scenario:** mark tests that require dual-stack provisioning.

```python
import pytest

@pytest.mark.env_req({"environment_def": {"board": {"eRouter_Provisioning_mode": ["dual"]}}})
def test_tr069_dual_mode(device_manager):
    ...
```

During `pytest_runtest_setup`, the plugin validates the marker against the loaded `boardfarm_config.env_config`. If matched, the plugin also runs the `contingency_check` hook to ensure devices are healthy before test execution.

---

## Running tests — examples

Run pytest and let boardfarm provision the environment as part of test setup.
(typical invocation — boardfarm CLI args are forwarded by the plugin):

```bash
pytest -s \
    --rootdir=. \
    --board-name prplos-docker-1 \
    --env-config ./boardfarm3/configs/boardfarm_env_example.json  \
    --inventory-config ./boardfarm3/configs/boardfarm_config_example.json \
    --junitxml ./results/pytest_run_report.xml \
    --html=./results/pytest_run_report.html  \
    --self-contained-html  \
    --save-console-logs=./results  \
    ./tests/
```

- The pytest-boardfarm plugin reads the --env-config and --inventory-config options and uses them to build a `BoardfarmConfig` and a `DeviceManager`.
- Unless you pass `--skip-boot`, the plugin will call Boardfarm pluggy hooks to reserve, boot and configure services and devices before tests run.
- During tests, fixtures like `device_manager` and `boardfarm_config` become available for use cases and tests.
- After the run, boardfarm plugin will run device teardown and release hooks, and store the collected logs/reports in `./results` directory.

### `--skip-contingency-checks` option

When passed, boardfarm will skip running the per-device **`contingency_check`** hooks that normally run just before a test starts (or during provisioning) to validate that devices/services are healthy and meet the test’s `env_req` expectations.

#### Where contingency checks run

The plugin calls device-level `contingency_check(env_req, device_manager)` hooks when a test is about to run (if the test has an `@pytest.mark.env_req(...)`) or during provisioning to ensure devices are responsive and in the expected state.

These checks typically run commands like TR-069 calls, IP checks, or basic service pings on each device.

#### Why you might use `--skip-contingency-checks`

- Faster iteration during development (avoid waiting for slow health checks).
- Quick smoke runs where you don’t want the plugin to gate tests.
- When contingency checks are known to be flaky and you’re debugging other layers.

#### Risks / tradeoffs (important)

- You may run tests against **unhealthy or misconfigured devices**. Skipping checks removes a safety gate that would otherwise detect unreachable consoles, missing services or mis-provisioned DUTs.

- **More flaky failures:** tests may fail with confusing symptoms because the device wasn’t validated first.

- **Harder root-cause:** the bug might be environment-related (power, network, container not up), but you’ll only see it when tests fail — later in the cycle.

#### Recommendation

Use `--skip-contingency-checks` **only** for short development loops or when you explicitly know the environment is already healthy. For CI and official runs, prefer **not** to skip contingency checks so tests are executed against validated devices.

## How the plugin orchestrates Boardfarm

High-level lifecycle the plugin implements:

1. `pytest` starts and early fixtures are registered.
2. When `BoardfarmPlugin` is active it adds Boardfarm CLI args and, on session start:
   - Calls the `boardfarm_reserve_devices` hook to reserve lab hardware or otherwise prepare inventory.
   - Calls the `boardfarm_parse_config` hook to merge inventory, env JSON and CLI overrides into a `BoardfarmConfig`.
3. During the test run the plugin:
   - Registers and instantiates device classes via `boardfarm_register_devices`.
   - Calls `boardfarm_setup_env` (async-capable) which triggers device-level hooks to boot and configure servers, devices and attached clients in the documented order.
4. Tests execute and call use-cases that use templated APIs; `DeviceManager` supplies the correct concrete implementation at runtime.
5. After tests complete the plugin calls `boardfarm_release_devices` and device shutdown hooks to clean up resources.

Because the plugin uses Boardfarm’s pluggy hooks for the heavy lifting, tests remain concise and protocol-driven while the plugin ensures correct lifecycle orchestration.

## HTML report integration

When `pytest-html` is present, the plugin enhances the generated HTML report by:

- Adding columns for test start time and hidden epoch time for sorting.
- Appending a Boardfarm section to the summary that shows deployment, environment and teardown details.
- Embedding captured PNG images attached to test results into the HTML output.
    > **Note:** This feature is only available when a GUI test performs a screen shot and the fixture saves the attachment.

This provides a compact test execution summary together with environment metadata and visual evidence useful for debugging.

## Troubleshooting & tips

- **Plugin not loaded:** make sure the plugin package is installed and the pytest entry points are configured. Use pytest's plugin diagnostics to verify loaded plugins.
- **HTML report not showing Boardfarm data:** confirm `pytest-html` is installed and enabled; the plugin only augments the HTML report when the html plugin is available.
- **Tests skipped via `env_req`:** verify that the `env_req` marker matches the keys and values declared in your `env_config`. Use the `boardfarm_config` fixture in a quick test to inspect resolved environment values.
- **Test selection edge cases:** the test selection option does pattern matching; ensure you provide normalized logical names that correspond to the collected test items.

## Development notes

- The plugin exposes a minimal set of early fixtures so small helper functionality can be used even when full deployment is not performed.
- The `BoardfarmPlugin` uses hookwrapper-style pytest hooks to capture setup and teardown logs and to integrate cleanly with pytest's logging plugin.
- For extending functionality, add command-line args via `boardfarm_add_cmdline_args`, register device classes using `boardfarm_add_devices` / `boardfarm_register_devices`, and implement device hooks in plugin packages.

## Contributing

Contributions are welcome. When adding or modifying plugin behavior follow these guidelines:

- Expose new CLI options via the `boardfarm_add_cmdline_args` hook so they participate in the standard parsing lifecycle.
- New device classes should be registered through `boardfarm_add_devices`, and any lifecycle orchestration should use core hooks rather than modifying runner internals.
- Add tests for fixture behavior using pytest's testing helpers and ensure HTML reporting integration remains intact where applicable.

## License

The pytest-boardfarm3 plugin follows the same licensing as Boardfarm (Clear BSD). See the top-level [LICENSE](https://github.com/lgirdk/pytest-boardfarm/blob/boardfarm3/LICENSE) file for details.
