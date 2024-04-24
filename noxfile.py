"""Lint and test pytest-boardfarm on multiple python environments."""

import nox

_PYTHON_VERSIONS = ["3.11"]

# Fail nox session when run a program which
# is not installed in its virtualenv
nox.options.error_on_external_run = True


@nox.session(python=_PYTHON_VERSIONS)
def lint(session: nox.Session) -> None:
    """Lint pytest-boardfarm.

    # noqa: DAR101
    """
    session.install("--upgrade", "--pre", "boardfarm3")
    session.install("--upgrade", ".[dev]")
    session.run("ruff", "format", "--check", ".")
    session.run("ruff", "check", ".")
    session.run("mypy", "pytest_boardfarm3")
    session.run("darglint2", "-s", "sphinx", "-x", "pytest_boardfarm3")


@nox.session(python=_PYTHON_VERSIONS)
def pylint(session: nox.Session) -> None:
    """Lint pytest-boardfarm using pylint without dev dependencies.

    # noqa: DAR101
    """
    session.install("--upgrade", "--pre", "boardfarm3")
    session.install("--upgrade", ".", "pylint")
    session.run("pylint", "pytest_boardfarm3")


@nox.session(python=_PYTHON_VERSIONS)
def test(session: nox.Session) -> None:
    """Test pytest-boardfarm.

    # noqa: DAR101
    """
    session.install("--upgrade", "--pre", "boardfarm3")
    session.install("--upgrade", ".[test]")
    session.run("pytest", "unittests")


@nox.session(python=_PYTHON_VERSIONS)
def boardfarm_help(session: nox.Session) -> None:
    """Execute boardfarm --help.

    This helps identifying integration issues with the plugins/devices.
    # noqa: DAR101
    """
    session.install("--upgrade", "--pre", "boardfarm3")
    session.install("--upgrade", "-e", ".")
    session.run("boardfarm", "--help")
