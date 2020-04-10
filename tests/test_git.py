"""Tests for git module."""
from pathlib import Path
import subprocess  # noqa: S404

import pytest

from poetry_up import git


def test_switch_create_without_location(repository: Path) -> None:
    """It creates the branch at master when master is checked out."""
    git.switch("topic", create=True)
    assert git.resolve_branch("topic") == git.resolve_branch("master")


def test_push_with_merge_request(repository: Path) -> None:
    """It raises an error when the remote does not support push options."""
    with pytest.raises(subprocess.CalledProcessError):
        # fatal: the receiving end does not support push options
        merge_request = git.MergeRequest("title", "description")
        git.push("origin", "master", merge_request=merge_request)
