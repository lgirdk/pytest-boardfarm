"""pytest boardfarm exception."""

from boardfarm3.exceptions import BoardfarmException


class BoardfarmPluginError(BoardfarmException):
    """Raise this on boardfarm plugin related error."""
