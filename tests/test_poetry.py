"""Tests for poetry module."""
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from poetry.factory import Factory
from poetry.packages import Package
from poetry.poetry import Poetry
from poetry.puzzle.provider import Provider
import pretend
import pytest
import tomlkit

from poetry_up import poetry


@pytest.mark.parametrize("source_type", ["vcs", "file", "directory"])
def test_search_for_package_with_provider_succeeds(
    monkeypatch: MonkeyPatch, repository: Path, source_type: str
) -> None:
    """It searches for the package using Provider."""
    poetry_instance = Factory().create_poetry(Path.cwd())
    locked_repository = poetry_instance.locker.locked_repository()
    for package in locked_repository.packages:
        if package.name == "marshmallow":
            break

    for requirement in poetry_instance.package.requires:
        if requirement.name == "marshmallow":
            monkeypatch.setattr(requirement, f"is_{source_type}", lambda: True)

    monkeypatch.setattr(
        Provider, f"search_for_{source_type}", lambda self, requirement: [package]
    )

    result = poetry.search_for_package_with_provider(poetry_instance, package)
    assert result is package


def test_search_for_package_with_provider_raises_if_package_not_found(
    repository: Path,
) -> None:
    """It raises an exception if the package was not found."""
    poetry_instance = Factory().create_poetry(Path.cwd())
    package = pretend.stub(name="no-such-package")

    with pytest.raises(ValueError):
        poetry.search_for_package_with_provider(poetry_instance, package)


def test_search_for_package_with_provider_raises_if_requirement_not_applicable(
    repository: Path,
) -> None:
    """It raises an exception if the package was not found."""
    poetry_instance = Factory().create_poetry(Path.cwd())
    locked_repository = poetry_instance.locker.locked_repository()
    for package in locked_repository.packages:
        if package.name == "marshmallow":
            break

    with pytest.raises(ValueError):
        poetry.search_for_package_with_provider(poetry_instance, package)


@pytest.mark.parametrize("source_type", ["git", "file", "directory"])
def test_find_latest_package_uses_provider(
    monkeypatch: MonkeyPatch, repository: Path, source_type: str
) -> None:
    """It uses Provider if applicable."""
    poetry_instance = Factory().create_poetry(Path.cwd())
    stub = pretend.call_recorder(lambda poetry, package: package)
    monkeypatch.setattr("poetry_up.poetry.search_for_package_with_provider", stub)
    package = pretend.stub(source_type=source_type)
    poetry.find_latest_package(poetry_instance, package)

    assert stub.calls


def test_show_outdated_skips_up_to_date_packages(
    monkeypatch: MonkeyPatch, repository: Path
) -> None:
    """It skips up-to-date packages."""

    def stub(poetry: Poetry, package: Package) -> Package:
        return package

    monkeypatch.setattr("poetry_up.poetry.find_latest_package", stub)
    assert not list(poetry.show_outdated())


@pytest.mark.parametrize("lock", [False, True])
def test_update_runs_subprocess(
    monkeypatch: MonkeyPatch, package: poetry.Package, lock: bool
) -> None:
    """It runs a subprocess."""
    stub = pretend.call_recorder(lambda *args, **kwargs: None)

    monkeypatch.setattr("subprocess.run", stub)
    poetry.update(package, lock=lock)

    assert stub.calls


def test_update_updates_version_constraints(
    monkeypatch: MonkeyPatch, repository: Path, package: poetry.Package
) -> None:
    """It updates version constraints in pyproject.toml if required."""
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: None)

    package.compatible = False
    poetry.update(package)

    config = Path("pyproject.toml")

    with config.open() as io:
        contents = io.read()

    document = tomlkit.loads(contents)
    constraint = document["tool"]["poetry"]["dependencies"]["marshmallow"]
    assert constraint == f"^{package.new_version}"


def test_update_constraint_updates_version_key(
    repository: Path, package: poetry.Package
) -> None:
    """It updates ``version`` keys in the dependencies table."""
    config = Path("pyproject.toml")

    with config.open() as io:
        contents = io.read()

    document = tomlkit.loads(contents)
    dependencies = document["tool"]["poetry"]["dependencies"]
    dependencies["marshmallow"] = {"version": dependencies["marshmallow"]}

    poetry.update_constraint(package, dependencies)

    assert dependencies["marshmallow"]["version"] == f"^{package.new_version}"
