"""Interact with console, wan, lan, wlan connections and re-run tests."""
# Copyright (c) 2015
#
# All rights reserved.
#
# This file is distributed under the Clear BSD license.
# The full text can be found in LICENSE in the root directory.

import logging
import os
import sys

import boardfarm
import pytest
from boardfarm import lib, tests
from boardfarm.lib.DeviceManager import get_device_by_name
from termcolor import colored

logger = logging.getLogger("bft")


def print_dynamic_devices(devices):
    """Print dynamic devices."""
    for device in devices:
        if (
            hasattr(device, "username")
            and hasattr(device, "ipaddr")
            and hasattr(device, "port")
        ):
            print(
                f"  {device.name} device:    ssh {device.username}@{device.ipaddr}:{device.port}"
            )
        else:
            print(f"  {device.name} device:")


def run_pytest_test(test):
    cmd_args = ["-s", "--disable-warnings", "-p", "no:randomly"]
    if os.getenv("BFT_DEBUG", "n").lower() == "y":
        cmd_args.append("-vv")
    if not test:
        cmd_args.append("--collect-only")
    # to be defined in a better way
    if "/" not in test:
        dirs = [
            "boardfarm/boardfarm/tests/",
            "boardfarm-lgi/boardfarm_lgi/tests/",
            "boardfarm-lgi-shared/boardfarm_lgi_shared/tests/",
            "boardfarm-docsis/boardfarm_docsis/tests/",
            "boardfarm-lgi-conn-oemqa-tests/boardfarm_lgi_conn_oemqa_tests/tests/",
            "boardfarm-lgi-conn-demo/tests/",
        ]
        cmd_args.extend(["-k", test] + dirs)
    else:
        cmd_args.extend([test])
    pytest.main(cmd_args)


def test_interact(devices):
    board = devices.board
    msg = colored(
        "Interactive console test",
        color="green",
        attrs=["bold"],
    )

    lib.common.test_msg(f"{msg}\nPress Ctrl-] to stop interaction and return to menu")
    board.sendline()
    try:
        board.interact()
    except Exception as error:
        print(error)
        return

    name_list = [i["name"] for i in board.config.get("devices")]

    while True:
        print("\n\nCurrent station")
        print("  Board console: %s" % board.config.get("conn_cmd"))
        print_dynamic_devices(board.dev)
        print(
            "Pro-tip: Increase kernel message verbosity with\n"
            '    echo "7 7 7 7" > /proc/sys/kernel/printk'
        )
        print("Menu")
        i = 2
        if board.consoles is None:
            print("  1: Enter console")
            i += 1
        else:
            i = 1
            for _ in board.consoles:
                print("  %s: Enter console" % i)
                i += 1

        print("  %s: List all tests" % i)
        i += 1
        print("  %s: Run test" % i)
        i += 1
        print("  %s: Reset board" % i)
        i += 1
        print("  %s: Enter interactive python shell" % i)
        i += 1
        if len(name_list) > 0:
            print(f"  Type a device name to connect: {name_list}")
        print("  x: Exit")
        key = input("Please select: ")

        if key in name_list:
            d = get_device_by_name(key)
            d.interact()

        i = 1
        for c in board.consoles:
            if key == str(i):
                c.interact()
            i += 1

        if key == str(i):
            run_pytest_test("")
            continue
        i += 1
        if key == str(i):
            try:
                tests.init(board.config)
            except Exception as e:
                print("Unable to re-import tests!")
                print(e)
            else:
                logger.error("Type test to run: ")
                test = sys.stdin.readline().strip()
                if test == "":
                    logger.error(
                        colored(
                            "Empty string in input, try again!",
                            color="red",
                            attrs=["bold"],
                        )
                    )
                    continue
                if test in tests.available_tests and issubclass(
                    tests.available_tests[test],
                    boardfarm.tests.bft_base_test.BftBaseTest,
                ):
                    logger.info(f"\nRunning legacy bft test {test}\n")
                else:
                    logger.info(f"\nRunning pytest {test}\n")
                run_pytest_test(test)
            continue
        i += 1
        if key == str(i):
            board.reset()
            print("Press Ctrl-] to stop interaction and return to menu")
            board.interact()
            continue
        i += 1

        if key == str(i):
            print("Enter python shell, press Ctrl-D to exit")
            try:
                import readline  # optional, will allow Up/Down/History in the console

                assert readline  # silence pyflakes
                import code

                vars = globals().copy()
                vars.update(locals())
                shell = code.InteractiveConsole(vars)
                shell.interact()
            except Exception as error:
                print(error)
                print("Unable to spawn interactive shell!")
            continue
        i += 1

        if key == "x":
            break
