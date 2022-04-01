"""pytest boardfarm exception."""

from boardfarm.exceptions import BoardfarmException


class BoardfarmPluginError(BoardfarmException):
    """Raise this on boardfarm plugin related error."""
