"""Poetry wrapper."""
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Iterator

from poetry.factory import Factory
from poetry.installation import Installer
from poetry.io.null_io import NullIO
from poetry.packages import Package as Package_
from poetry.poetry import Poetry
from poetry.puzzle.provider import Provider
from poetry.semver import parse_constraint
from poetry.utils.env import EnvManager
from poetry.version.version_selector import VersionSelector
import tomlkit  # noqa: E402
import tomlkit.api  # noqa: E402


sys.path.pop(0)  # Remove Poetry's vendor directory from sys.path.


@dataclass
class Package:
    """Package with current and available versions."""

    name: str
    old_version: str
    new_version: str
    compatible: bool = True


def search_for_package_with_provider(poetry: Poetry, package: Package_) -> Package_:
    """Search for the package using Provider."""
    requires = poetry.package.requires + poetry.package.dev_requires

    for requirement in requires:
        if requirement.name == package.name:
            provider = Provider(poetry.package, poetry.pool, NullIO())

            if requirement.is_vcs():
                return provider.search_for_vcs(requirement)[0]
            if requirement.is_file():
                return provider.search_for_file(requirement)[0]
            if requirement.is_directory():
                return provider.search_for_directory(requirement)[0]

    raise ValueError(f"package {package.name} not found in requirements")


def find_latest_package(poetry: Poetry, package: Package_) -> Package_:
    """Find the latest package."""
    if package.source_type in ("git", "file", "directory"):
        return search_for_package_with_provider(poetry, package)

    selector = VersionSelector(poetry.pool)
    return selector.find_best_candidate(
        package.name, ">={}".format(package.pretty_version)
    )


def show_outdated() -> Iterator[Package]:
    """Yield outdated packages."""
    poetry = Factory().create_poetry(Path.cwd())
    repository = poetry.locker.locked_repository(with_dev_reqs=True)

    for package in repository.packages:
        latest = find_latest_package(poetry, package)
        constraint = parse_constraint(f"^{package.pretty_version}")
        compatible = latest.version and constraint.allows(latest.version)
        if package.version != latest.version:
            yield Package(
                package.pretty_name,
                str(package.version),
                str(latest.version),
                compatible,
            )


def update_constraint(package: Package, dependencies: tomlkit.api.Table) -> None:
    """Update the version constraint for the package in the given TOML table."""
    for dependency, value in dependencies.items():
        if dependency == package.name:
            constraint = f"^{package.new_version}"

            if isinstance(value, str):
                dependencies[dependency] = constraint
            else:
                dependencies[dependency]["version"] = constraint

            break


def update_pyproject_toml(package: Package) -> None:
    """Update the version constraint for the package in pyproject.toml."""
    config = Path("pyproject.toml")

    with config.open() as io:
        contents = io.read()
        document = tomlkit.loads(contents)

    for key in ("dependencies", "dev-dependencies"):
        dependencies = document["tool"]["poetry"][key]
        update_constraint(package, dependencies)

    updated_contents = tomlkit.dumps(document)
    with config.open(mode="w") as io:
        io.write(updated_contents)


def update(package: Package, lock: bool = False) -> None:
    """Update the given package.

    Args:
        package: The package to be updated.
        lock: If True, do not install the package into the environment.
    """
    if not package.compatible:
        update_pyproject_toml(package)

    poetry = Factory().create_poetry(Path.cwd())
    env_manager = EnvManager(poetry)
    io = NullIO()
    env = env_manager.create_venv(io)

    installer = Installer(io, env, poetry.package, poetry.locker, poetry.pool)
    installer.whitelist({package.name: "*"})
    installer.dev_mode(True)
    installer.execute_operations(not lock)
    installer.update(True)
    installer.run()
