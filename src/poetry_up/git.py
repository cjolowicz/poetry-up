"""Git wrapper."""
from dataclasses import dataclass
import subprocess  # noqa: S404
from typing import Iterable


def current_branch() -> str:
    """Return the checked out branch."""
    process = subprocess.run(  # noqa: S603, S607
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return process.stdout.strip()


def is_clean(paths: Iterable[str] = ()) -> bool:
    """Return True if the working tree, or the given files, are clean."""
    args = ["git", "diff", "--quiet", "--exit-code", *paths]
    process = subprocess.run(args)  # noqa: S603, S607
    return process.returncode == 0


def branch_exists(branch: str) -> bool:
    """Return True if the branch exists."""
    process = subprocess.run(  # noqa: S603, S607
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"]
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
        subprocess.run(  # noqa: S603, S607
            ["git", "switch", "--quiet", "--create", branch, location], check=True
        )
    elif create:
        subprocess.run(  # noqa: S603, S607
            ["git", "switch", "--quiet", "--create", branch], check=True
        )
    else:
        subprocess.run(  # noqa: S603, S607
            ["git", "switch", "--quiet", branch], check=True
        )


def resolve_branch(branch: str) -> str:
    """Return the SHA1 hash for the given branch."""
    process = subprocess.run(  # noqa: S603, S607
        ["git", "rev-parse", f"refs/heads/{branch}"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return process.stdout.strip()


def remove_branch(branch: str) -> None:
    """Remove the specified branch."""
    subprocess.run(  # noqa: S603, S607
        ["git", "branch", "--quiet", "--delete", branch], check=True
    )


def add(paths: Iterable[str]) -> None:
    """Add the specified paths to the index."""
    subprocess.run(["git", "add", *paths], check=True)  # noqa: S603, S607


def commit(message: str) -> None:
    """Create a commit using the given message."""
    subprocess.run(  # noqa: S603, S607
        ["git", "commit", "--quiet", f"--message={message}"], check=True
    )


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
    args = ["git", "push", "--set-upstream", remote, branch]
    if merge_request is not None:
        args += [
            "--push-option=merge_request.create",
            f"--push-option=merge_request.title={merge_request.title}",
            f"--push-option=merge_request.description={merge_request.description}",
        ]
    subprocess.run(args, check=True)  # noqa: S603, S607
