"""Lint and test pytest-boardfarm on multiple python environments."""

import nox

_PYTHON_VERSIONS = ["3.11"]

# Fail nox session when run a program which
# is not installed in its virtualenv
nox.options.error_on_external_run = True


@nox.session(python=_PYTHON_VERSIONS)
def lint(session: nox.Session) -> None:
    """Lint pytest-boardfarm."""
    session.install("--upgrade", "--pre", "boardfarm3")
    session.install("--upgrade", ".[dev]")
    session.run("black", ".", "--check")
    session.run("isort", ".", "--check-only")
    session.run("flake8", ".")
    session.run("mypy", "pytest_boardfarm3")


@nox.session(python=_PYTHON_VERSIONS)
def pylint(session: nox.Session) -> None:
    """Lint pytest-boardfarm using pylint without dev dependencies."""
    session.install("--upgrade", "--pre", "boardfarm3")
    session.install("--upgrade", ".", "pylint")
    session.run("pylint", "pytest_boardfarm3")


@nox.session(python=_PYTHON_VERSIONS)
def test(session: nox.Session) -> None:
    """Test pytest-boardfarm."""
    session.install("--upgrade", "--pre", "boardfarm3")
    session.install("--upgrade", ".[test]")
    session.run("pytest", "unittests")
