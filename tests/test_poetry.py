"""Tests for poetry module."""
import contextlib
from pathlib import Path
from typing import Any

from _pytest.monkeypatch import MonkeyPatch
import pretend
import pytest

from poetry_up import poetry


description = (
    "A lightweight library for converting complex datatypes"
    " to and from native Python datatypes."
    "\n"
)


def test_show_outdated_matches_valid_output(
    monkeypatch: MonkeyPatch, package: poetry.Package
) -> None:
    """It matches valid output."""

    def stub(*args: Any, **kwargs: Any) -> Any:
        return pretend.stub(
            stdout=" ".join(
                (package.name, package.old_version, package.new_version, description)
            )
        )

    monkeypatch.setattr("subprocess.run", stub)
    assert package in poetry.show_outdated()


def test_show_outdated_skips_unexpected_output(monkeypatch: MonkeyPatch) -> None:
    """It skips unpexpected output."""

    def stub(*args: Any, **kwargs: Any) -> Any:
        return pretend.stub(stdout="Surprise!")

    monkeypatch.setattr("subprocess.run", stub)
    assert not tuple(poetry.show_outdated())


@pytest.mark.parametrize("lock", [False, True])
@pytest.mark.parametrize("latest", [False, True])
def test_update_runs_subprocess(
    monkeypatch: MonkeyPatch, package: poetry.Package, lock: bool, latest: bool
) -> None:
    """It runs a subprocess."""
    stub = pretend.call_recorder(lambda *args, **kwargs: None)

    monkeypatch.setattr("subprocess.run", stub)
    poetry.update(package, lock=lock, latest=latest)

    assert stub.calls


def get_dependency(config: poetry._Config, package: str) -> Any:
    """Return the package entry from the dependencies table."""
    return config._config["dependencies"][package]


def set_dependency(config: poetry._Config, package: str, value: Any) -> None:
    """Insert the package entry into the dependencies table."""
    config._config["dependencies"][package] = value


def test_config_update_constraint_string(
    package: poetry.Package, repository: Path
) -> None:
    """It updates version constraints that are a string literal."""
    config = poetry._Config()
    config.update_constraint(package)

    assert package.new_version == get_dependency(config, package.name)[1:]


def test_config_update_constraint_table(
    package: poetry.Package, repository: Path
) -> None:
    """It updates version constraints that are a table."""
    config = poetry._Config()
    version = get_dependency(config, package.name)
    set_dependency(config, package.name, {"version": version})

    config.update_constraint(package)

    assert package.new_version == get_dependency(config, package.name)["version"][1:]


def test_config_update_constraint_unknown(
    package: poetry.Package, repository: Path
) -> None:
    """It preserves version constraints with unknown syntax."""
    config = poetry._Config()
    version = get_dependency(config, package.name)
    set_dependency(config, package.name, {"unknown": version})

    config.update_constraint(package)

    assert {"unknown": version} == get_dependency(config, package.name)


def test_config_exit(package: poetry.Package, repository: Path) -> None:
    """It does not write on errors."""
    old_constraint = get_dependency(poetry._Config(), package.name)

    with contextlib.suppress(RuntimeError):
        with poetry._Config() as config:
            config.update_constraint(package)
            raise RuntimeError("boom")

    assert old_constraint == get_dependency(poetry._Config(), package.name)
