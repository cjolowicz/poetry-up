"""Package-wide test fixtures."""
import contextlib
import os
from pathlib import Path
import subprocess  # noqa: S404
from typing import Iterator

import pytest

from poetry_up import poetry


@contextlib.contextmanager
def working_directory(directory: Path) -> Iterator[None]:
    """Context manager to change the working directory."""
    cwd = Path.cwd()
    try:
        os.chdir(directory)
        yield
    finally:
        os.chdir(cwd)


@pytest.fixture
def repository(shared_datadir: Path, tmp_path: Path) -> Iterator[Path]:
    """Git repository with Poetry project."""
    remote_repository = tmp_path / "remote-repository"
    remote_repository.mkdir()

    for filename in ["pyproject.toml", "poetry.lock"]:
        source = shared_datadir / filename
        destination = remote_repository / filename
        destination.write_text(source.read_text())

    commands = [
        ["git", "init"],
        ["git", "add", "."],
        ["git", "commit", "--message=Initial import"],
    ]
    for command in commands:
        subprocess.run(command, check=True, cwd=remote_repository)  # noqa: S603, S607

    local_repository = tmp_path / "local-repository"
    subprocess.run(  # noqa: S603, S607
        ["git", "clone", str(remote_repository), str(local_repository)], check=True
    )
    with working_directory(local_repository):
        yield local_repository


@pytest.fixture
def package() -> poetry.Package:
    """Package to be upgraded."""
    return poetry.Package("marshmallow", "3.0.0", "3.5.1")
