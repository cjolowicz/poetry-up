"""Tests for poetry module."""
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from poetry.packages import Package
from poetry.puzzle.provider import Provider
import pretend
import pytest
import tomlkit

from poetry_up.poetry import Package as PackageUpdate
from poetry_up.poetry import Poetry, update_constraint, update_pyproject_toml


class TestSearchForPackageWithProvider:
    """Tests for Poetry._search_for_package_with_provider."""

    @pytest.mark.parametrize("source_type", ["vcs", "file", "directory"])
    def test_it_succeeds(
        self, monkeypatch: MonkeyPatch, repository: Path, source_type: str
    ) -> None:
        """It searches for the package using Provider."""
        poetry = Poetry()
        locked_repository = poetry._poetry.locker.locked_repository()
        for package in locked_repository.packages:
            if package.name == "marshmallow":
                break

        for requirement in poetry._poetry.package.requires:
            if requirement.name == "marshmallow":
                monkeypatch.setattr(requirement, f"is_{source_type}", lambda: True)

        monkeypatch.setattr(
            Provider, f"search_for_{source_type}", lambda self, requirement: [package]
        )

        result = poetry.search_for_package_with_provider(package)
        assert result is package

    def test_it_raises_if_package_not_found(self, repository: Path) -> None:
        """It raises an exception if the package was not found."""
        poetry = Poetry()
        package = pretend.stub(name="no-such-package")

        with pytest.raises(ValueError):
            poetry._search_for_package_with_provider(package)

    def test_it_raises_if_requirement_not_applicable(self, repository: Path) -> None:
        """It raises an exception if the package was not found."""
        poetry = Poetry()
        locked_repository = poetry._poetry.locker.locked_repository()
        for package in locked_repository.packages:
            if package.name == "marshmallow":
                break

        with pytest.raises(ValueError):
            poetry._search_for_package_with_provider(package)


class TestFindLatestPackage:
    """Tests for Poetry._find_latest_package."""

    @pytest.mark.parametrize("source_type", ["git", "file", "directory"])
    def test_it_uses_provider(
        self, monkeypatch: MonkeyPatch, repository: Path, source_type: str
    ) -> None:
        """It uses Provider if applicable."""
        poetry = Poetry()
        stub = pretend.call_recorder(lambda self, package: package)
        monkeypatch.setattr(poetry, "_search_for_package_with_provider", stub)
        package = pretend.stub(source_type=source_type)
        poetry._find_latest_package(package)

        assert stub.calls


class TestShowOutdated:
    """Tests for Poetry.show_outdated."""

    def test_it_skips_up_to_date_packages(
        self, monkeypatch: MonkeyPatch, repository: Path
    ) -> None:
        """It skips up-to-date packages."""

        def stub(self: Poetry, package: Package) -> Package:
            return package

        poetry = Poetry()
        monkeypatch.setattr(poetry, "_find_latest_package", stub)
        assert not list(poetry.show_outdated())


class TestUpdateConstraint:
    """Tests for update_constraint."""

    def test_it_updates_version_key(
        self, repository: Path, package: PackageUpdate
    ) -> None:
        """It updates ``version`` keys in the dependencies table."""
        config = Path("pyproject.toml")

        with config.open() as io:
            contents = io.read()

        document = tomlkit.loads(contents)
        dependencies = document["tool"]["poetry"]["dependencies"]
        dependencies["marshmallow"] = {"version": dependencies["marshmallow"]}

        update_constraint(package, dependencies)

        assert dependencies["marshmallow"]["version"] == f"^{package.new_version}"


class TestUpdatePyProjectTOML:
    """Tests for update_pyproject_toml."""

    def test_it_updates_version_constraints(
        self, repository: Path, package: PackageUpdate
    ) -> None:
        """It updates version constraints in pyproject.toml."""
        update_pyproject_toml(package)

        config = Path("pyproject.toml")
        with config.open() as io:
            contents = io.read()

        document = tomlkit.loads(contents)
        constraint = document["tool"]["poetry"]["dependencies"]["marshmallow"]
        assert constraint == f"^{package.new_version}"


class TestUpdate:
    """Tests for update."""

    @pytest.mark.parametrize("compatible", [True, False])
    def test_update_invokes_installer(
        self,
        monkeypatch: MonkeyPatch,
        repository: Path,
        package: PackageUpdate,
        compatible: bool,
    ) -> None:
        """It invokes Installer.run."""
        stub = pretend.call_recorder(lambda self: None)
        monkeypatch.setattr("poetry.installation.installer.Installer.run", stub)

        package.compatible = compatible
        poetry = Poetry()
        poetry.update(package)

        assert stub.calls
