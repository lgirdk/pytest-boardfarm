"""Lint and test pytest_boardfarm on multiple python environments."""
import nox

_PYTHON_VERSIONS = ["3.9"]
# Fail nox session when run a program which
# is not installed in its virtualenv
nox.options.error_on_external_run = True


def basic_install(session):
    session.install("--upgrade", "pip")
    session.install("--upgrade", "pip", "wheel")


@nox.session(python=_PYTHON_VERSIONS)
def lint(session: nox.Session) -> None:
    """Lint pytest_boardfarm."""
    basic_install(session)
    session.install("--upgrade", "pip", "wheel", ".[dev]")
    session.run("black", ".", "--check")
    session.run("isort", ".", "--check-only")
    session.run("flake8", "pytest_boardfarm")


@nox.session(python=_PYTHON_VERSIONS)
def pylint(session: nox.Session) -> None:
    """Lint pytest_boardfarm using pylint without dev dependencies."""
    basic_install(session)
    session.install("--upgrade", "pip", "wheel", ".", "pylint")
    session.run("pylint", "pytest_boardfarm")


@nox.session(python=_PYTHON_VERSIONS)
def test(session: nox.Session) -> None:
    """Test pytest_boardfarm."""
    basic_install(session)
    # FIXME: integration tests require boardfarm-lgi-shared.
    # a public package should not rely on a private one
    # boardfarm-lgi-shared also requires ftfy
    session.install(
        "--upgrade", "pip", "wheel", ".[test]", "boardfarm-lgi-shared", "ftfy"
    )
    session.run(
        "pytest",
        "integrationtests/",
    )
