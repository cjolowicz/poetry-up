"""Tests for github module."""
from typing import Any

from _pytest.monkeypatch import MonkeyPatch
import pretend
import pytest

from poetry_up import github


@pytest.mark.parametrize("branch", ["topic", "another-topic"])
def test_pull_request_exists(monkeypatch: MonkeyPatch, branch: str) -> None:
    """It matches the branch in the process output."""

    def stub(*args: Any, **kwargs: Any) -> Any:
        return pretend.stub(stdout="topic")

    with monkeypatch.context() as m:
        m.setattr("subprocess.run", stub)
        assert github.pull_request_exists(branch) is (branch == "topic")


def test_create_pull_request(monkeypatch: MonkeyPatch) -> None:
    """It runs a subprocess."""
    stub = pretend.call_recorder(lambda *args, **kwargs: None)

    with monkeypatch.context() as m:
        m.setattr("subprocess.run", stub)
        github.create_pull_request("title", "body")

    assert stub.calls
