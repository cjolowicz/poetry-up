"""Poetry wrapper."""
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess  # noqa: S404
from typing import Any
from typing import Iterator
from typing import Optional

import tomlkit


@dataclass
class Package:
    """Package with current and available versions."""

    name: str
    old_version: str
    new_version: str


_CANONICALIZE_PATTERN = re.compile(r"[-_.]+")


def _canonicalize_name(name: str) -> str:
    # From ``packaging.utils.canonicalize_name`` (PEP 503)
    return _CANONICALIZE_PATTERN.sub("-", name).lower()


class _Config:
    """Poetry configuration."""

    def __init__(self) -> None:
        """Initialize."""
        self._path = Path.cwd() / "pyproject.toml"
        self.load()

    def load(self) -> None:
        """Read the document from disk."""
        text = self._path.read_text(encoding="utf-8")
        self._data = tomlkit.parse(text)
        self._config = self._data["tool"]["poetry"]

    def write(self) -> None:
        """Write the document back to disk."""
        text = tomlkit.dumps(self._data)
        self._path.write_text(text, encoding="utf-8")

    def __enter__(self) -> "_Config":
        """Enter the runtime context."""
        return self

    def __exit__(
        self, exception_type: Any, exception: Optional[BaseException], traceback: Any
    ) -> None:
        """Enter the runtime context."""
        if exception is None:
            self.write()

    def update_constraint(self, package: Package) -> None:
        """Update the constraint for the given package."""
        groups = [self._config["dependencies"], self._config["dev-dependencies"]]
        for dependencies in groups:
            for dependency, value in dependencies.items():
                if _canonicalize_name(dependency) == _canonicalize_name(package.name):
                    if isinstance(value, str):
                        dependencies[dependency] = f"^{package.new_version}"
                    elif "version" in value:
                        dependencies[dependency]["version"] = f"^{package.new_version}"
                    return


def show_outdated() -> Iterator[Package]:
    """Yield outdated packages."""
    package = "[a-z][-a-z0-9]*"
    version = "[0-9][.0-9a-z]*"
    separator = "[ (!)]*"
    pattern = re.compile(f"({package}) +{separator}({version}) +({version}) +")
    process = subprocess.run(  # noqa: S603, S607
        ["poetry", "show", "--outdated", "--no-ansi"],
        check=True,
        capture_output=True,
        text=True,
    )
    for line in process.stdout.splitlines():
        match = pattern.match(line)
        if match is None:
            continue
        yield Package(*match.group(1, 2, 3))


def update(package: Package, lock: bool = False, latest: bool = False) -> None:
    """Update the given package.

    Args:
        package: The package to be updated.
        lock: If True, do not install the package into the environment.
        latest: If True, update the version constraint when required.
    """
    options = ["--lock"] if lock else []

    if latest:
        with _Config() as config:
            config.update_constraint(package)

    subprocess.run(  # noqa: S603, S607
        ["poetry", "update", *options, package.name], check=True, capture_output=True
    )
