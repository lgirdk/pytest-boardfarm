"""Unit tests for utils module in pytest-boardfarm."""

import pytest

from pytest_boardfarm3.lib.utils import is_env_matching

env_boot_file = {
    "environment_def": {
        "board": {
            "boot_file": "Main eRouter Mode */\n        VendorSpecific\n ",
            "eRouter_Provisioning_mode": "dual",
        },
    },
    "version": "1.0",
}


@pytest.mark.parametrize(
    ("contains_check", "contains_check_value", "expected"),
    [
        ("contains_exact", "VendorSpecific", True),
        ("not_contains_exact", "single", True),
        ("contains_regex", r"Main\seRouter\sMode\s\*/", True),
        ("not_contains_regex", r"Main\teRouter\sMode\s\*/", True),
        ("contains_exact", "single", False),
        ("not_contains_exact", "VendorSpecific", False),
        ("contains_regex", r"Main\teRouter\sMode\s\*/", False),
        ("not_contains_regex", r"Main\seRouter\sMode\s\*/", False),
    ],
)
def test_contains_check(
    contains_check: str,
    contains_check_value: str,
    expected: bool,
) -> None:
    """Unit tests with positive and negative scenarios for `contains_` check.

    :param contains_check: contains_check name, for ex: contains_exact
    :type contains_check: str
    :param contains_check_value: value to be checked against boardfarm env
    :type contains_check_value: str
    :param expected: expected value from running the tests
    :type expected: bool
    """
    test_req = {
        "environment_def": {
            "board": {"boot_file": [{contains_check: contains_check_value}]},
        },
    }
    assert is_env_matching(test_req, env_boot_file) == expected


@pytest.mark.parametrize(
    "unknown_contains_check_list",
    [
        [
            {"contains_abc": "VendorSpecific"},
        ],
        [
            {"contains_exact": "VendorSpecific"},
            {"contains_abc": "single"},
        ],
        [
            {"contains_abc": "VendorSpecific"},
            {"contains_efg": "single"},
            {"contains_hij": "dual"},
        ],
        [
            {"contains_abc": "VendorSpecific"},
            {"contains_efg": "single"},
            {"contains_exact": "VendorSpecific"},
            {"contains_regex": r"Main\seRouter\sMode\s\*/"},
        ],
    ],
)
def test_unknown_contains_check(
    unknown_contains_check_list: list[dict[str, str]],
) -> None:
    """Unit test to check for an unknown check in test_env_req.

    :param unknown_contains_check_list: list of dict containing combinations of unknown
                                        checks i.e; invalid keys
    :type unknown_contains_check_list: list[dict[str, str]]
    """
    test_req = {
        "environment_def": {"board": {"boot_file": unknown_contains_check_list}},
    }
    with pytest.raises(ValueError, match="Invalid contains checks"):
        is_env_matching(test_req, env_boot_file)


@pytest.mark.parametrize(
    ("contains_check_list", "expected"),
    [
        (
            [
                {"contains_exact": "VendorSpecific"},
                {"not_contains_exact": "single"},
                {"contains_regex": r"Main\seRouter\sMode\s\*/"},
                {"not_contains_regex": r"Main\teRouter\sMode\s\*/"},
            ],
            True,
        ),
        (
            [
                {"contains_exact": "VendorSpecific"},
                {"contains_exact": "single"},
                {"contains_regex": r"Main\seRouter\sMode\s\*/"},
                {"contains_regex": r"Main\teRouter\sMode\s\*/"},
            ],
            False,
        ),
        (
            [
                {"not_contains_exact": "VendorSpecific"},
                {"not_contains_exact": "single"},
                {"not_contains_regex": r"Main\seRouter\sMode\s\*/"},
                {"not_contains_regex": r"Main\teRouter\sMode\s\*/"},
            ],
            False,
        ),
        (
            [
                {"not_contains_exact": "VendorSpecific"},
                {"contains_exact": "single"},
                {"not_contains_regex": r"Main\seRouter\sMode\s\*/"},
                {"contains_regex": r"Main\teRouter\sMode\s\*/"},
            ],
            False,
        ),
        (
            [
                {"contains_exact": "VendorSpecific"},
                {"not_contains_exact": "single"},
                {"not_contains_regex": r"Main\teRouter\sMode\s\*/"},
                {"contains_regex": r"Main\seRouter\sMode\s\*/"},
            ],
            True,
        ),
        (
            [
                {"not_contains_exact": "VendorSpecific"},
                {"contains_exact": "single"},
                {"contains_regex": r"Main\seRouter\sMode\s\*/"},
                {"not_contains_regex": r"Main\teRouter\sMode\s\*/"},
            ],
            False,
        ),
        (
            [
                {"not_contains_exact": "VendorSpecific"},
                {"not_contains_exact": "single"},
                {"contains_regex": r"Main\seRouter\sMode\s\*/"},
                {"not_contains_regex": r"Main\teRouter\sMode\s\*/"},
            ],
            False,
        ),
        (
            [
                {"contains_exact": "VendorSpecific"},
                {"contains_exact": "single"},
                {"not_contains_regex": r"Main\seRouter\sMode\s\*/"},
                {"not_contains_regex": r"Main\teRouter\sMode\s\*/"},
            ],
            False,
        ),
    ],
)
def test_contains_check_combinations(
    contains_check_list: list[dict[str, str]],
    expected: bool,
) -> None:
    """Tests with positive and negative scenarios for combinations of `contains_` check.

    :param contains_check_list: list of dictionary containing combinations of
                                `contains_` checks
    :type contains_check_list: list[dict[str, str]]
    :param expected: expected value from running the tests
    :type expected: bool
    """
    test_req = {"environment_def": {"board": {"boot_file": contains_check_list}}}
    assert is_env_matching(test_req, env_boot_file) == expected
