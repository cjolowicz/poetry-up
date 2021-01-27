"""Poetry wrapper."""
from dataclasses import dataclass
import re
import subprocess  # noqa: S404
from typing import Iterator


@dataclass
class Package:
    """Package with current and available versions."""

    name: str
    old_version: str
    new_version: str


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


def update(package: str, lock: bool = False, latest: bool = False) -> None:
    """Update the given package.

    Args:
        package: The package to be updated.
        lock: If True, do not install the package into the environment.
        latest: If True, update the version constraint when required.
    """
    options = ["--lock"] if lock else []

    if latest:
        command = ["poetry", "add", *options, f"{package}@latest"]
    else:
        command = ["poetry", "update", *options, package]

    subprocess.run(command, check=True, capture_output=True)  # noqa: S603, S607
