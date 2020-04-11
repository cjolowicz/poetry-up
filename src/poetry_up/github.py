"""GitHub wrapper."""
import subprocess  # noqa: S404


def pull_request_exists(branch: str) -> bool:
    """Return True if a pull request exists for the given branch."""
    process = subprocess.run(  # noqa: S603, S607
        ["gh", "pr", "list"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return branch in process.stdout


def create_pull_request(title: str, body: str) -> None:
    """Create a pull request for the checked out branch."""
    subprocess.run(  # noqa: S603, S607
        ["gh", "pr", "create", f"--title={title}", f"--body={body}"], check=True
    )
