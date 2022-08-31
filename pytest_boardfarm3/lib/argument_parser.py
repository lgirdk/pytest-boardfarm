"""Wrapper to pytest argument parser."""

from typing import Any, Dict, Tuple

from _pytest.config.argparsing import OptionGroup, Parser


# pylint: disable-next=too-few-public-methods
class _OptionGroup:
    """Argument parser option group."""

    def __init__(self, group: OptionGroup):
        """Initialize option group."""
        self._group = group

    def add_argument(self, *args: Tuple, **kwargs: Dict[str, Any]) -> None:
        """Add argument to option group."""
        self._group.addoption(*args, **kwargs)  # type: ignore


class ArgumentParser:
    """Wrapper to pytest argument parser.

    Pytest is using a different method to add command line arguments.
    Boardfarm is using the standard argparser library. This wrapper
    converts boardfarm add arguments to pytest add argument way.
    """

    def __init__(self, parser: Parser) -> None:
        """Initialize argument parser wrapper."""
        self._parser = parser
        self._group = parser.getgroup("boardfarm", "boardfarm")

    # pylint: disable-next=unused-argument
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
