"""Wrapper to pytest argument parser."""

from typing import Any

from _pytest.config.argparsing import OptionGroup, Parser


# pylint: disable-next=too-few-public-methods
class _OptionGroup:
    """Argument parser option group."""

    def __init__(self, group: OptionGroup):
        """Initialize option group.

        :param group: argument group
        :type group: OptionGroup
        """
        self._group = group

    def add_argument(self, *args: tuple, **kwargs: dict[str, Any]) -> None:
        """Add argument to option group.

        :param args: positional arguments
        :type args: Tuple
        :param kwargs: keyword arguments
        :type kwargs: Dict[str, Any]
        """
        self._group.addoption(*args, **kwargs)  # type: ignore[arg-type]


class ArgumentParser:
    """Wrapper to pytest argument parser.

    Pytest is using a different method to add command line arguments.
    Boardfarm is using the standard argparser library. This wrapper
    converts boardfarm add arguments to pytest add argument way.
    """

    def __init__(self, parser: Parser) -> None:
        """Initialize argument parser wrapper.

        :param parser: pytest parser instance
        :type parser: Parser
        """
        self._parser = parser
        self._group = parser.getgroup("boardfarm", "boardfarm")

    def add_argument_group(  # pylint: disable-next=unused-argument
        self,
        name: str,
        *args: tuple,  # noqa: ARG002
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> _OptionGroup:
        """Add argument group to argument parser.

        :param name: group name
        :type name: str
        :param args: positional arguments
        :type args: Tuple
        :param kwargs: keyword arguments
        :type kwargs: Dict[str, Any]
        :return: argument group instance
        :rtype: _OptionGroup
        """
        group_name = f"boardfarm-{name}"
        group = self._parser.getgroup(group_name, group_name)
        return _OptionGroup(group)

    def add_argument(self, *args: tuple, **kwargs: dict[str, Any]) -> None:
        """Add argument to argument parser.

        :param args: positional arguments
        :type args: Tuple
        :param kwargs: keyword arguments
        :type kwargs: Dict[str, Any]
        """
        self._group.addoption(*args, **kwargs)  # type: ignore[arg-type]
