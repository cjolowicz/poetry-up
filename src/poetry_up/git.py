"""Git wrapper."""
from dataclasses import dataclass
import subprocess  # noqa: S404
from typing import Iterable


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Invoke git."""
    return subprocess.run(  # noqa: S603, S607
        ["git", *args], check=check, capture_output=True, text=True,
    )


def current_branch() -> str:
    """Return the checked out branch."""
    process = git("rev-parse", "--abbrev-ref", "HEAD")
    return process.stdout.strip()


def is_clean(paths: Iterable[str] = ()) -> bool:
    """Return True if the working tree, or the given files, are clean."""
    process = git("diff", "--quiet", "--exit-code", *paths, check=False)
    return process.returncode == 0


def branch_exists(branch: str) -> bool:
    """Return True if the branch exists."""
    process = git(
        "show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False
    )
    return process.returncode == 0


def switch(branch: str, create: bool = False, location: str = None) -> None:
    """Switch to the specified branch.

    Args:
        branch: The branch to be switched to.
        create: Create the branch.
        location: The location at which the branch should be created.
    """
    if create and location is not None:
        git("switch", "--create", branch, location)
    elif create:
        git("switch", "--create", branch)
    else:
        git("switch", branch)


def resolve_branch(branch: str) -> str:
    """Return the SHA1 hash for the given branch."""
    process = git("rev-parse", f"refs/heads/{branch}")
    return process.stdout.strip()


def remove_branch(branch: str) -> None:
    """Remove the specified branch."""
    git("branch", "--delete", branch)


def add(paths: Iterable[str]) -> None:
    """Add the specified paths to the index."""
    git("add", *paths)


def commit(message: str) -> None:
    """Create a commit using the given message."""
    git("commit", f"--message={message}")


@dataclass
class MergeRequest:
    """Merge request with a title and a description."""

    title: str
    description: str


def push(remote: str, branch: str, merge_request: MergeRequest = None) -> None:
    """Push the branch to the remote.

    Args:
        remote: The remote to push to.
        branch: The branch to be pushed.
        merge_request: The merge request to create for the branch (optional).
    """
    if merge_request is not None:
        git(
            "push",
            "--push-option=merge_request.create",
            f"--push-option=merge_request.title={merge_request.title}",
            f"--push-option=merge_request.description={merge_request.description}",
            "--set-upstream",
            remote,
            branch,
        )
    else:
        git("push", "--set-upstream", remote, branch)
