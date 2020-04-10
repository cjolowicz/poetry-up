"""Tests for poetry module."""
from typing import Any

from _pytest.monkeypatch import MonkeyPatch
import pretend
import pytest

from poetry_up import poetry


package = poetry.Package("marshmallow", "3.0.0", "3.5.1")
description = (
    "A lightweight library for converting complex datatypes"
    " to and from native Python datatypes."
    "\n"
)


def test_show_outdated_matches_valid_output(monkeypatch: MonkeyPatch) -> None:
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
def test_update_runs_subprocess(monkeypatch: MonkeyPatch, lock: bool) -> None:
    """It runs a subprocess."""
    stub = pretend.call_recorder(lambda *args, **kwargs: None)

    monkeypatch.setattr("subprocess.run", stub)
    poetry.update("marshmallow", lock=lock)

    assert stub.calls
