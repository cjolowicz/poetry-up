"""Command-line interface."""
import os
from typing import Tuple

import click

from . import __version__, git, github, poetry


program_name = "poetry-up"


def show_package(package: poetry.Package) -> None:
    """Print message describing the package upgrade."""
    message = "{}: {} → {}".format(
        click.style(package.name, fg="bright_green"),
        click.style(package.old_version, fg="blue"),
        click.style(package.new_version, fg="red"),
    )
    click.echo(message)


@click.command()  # noqa: C901
@click.option(
    "--install/--no-install",
    help="Install dependency into virtual environment.",
    default=True,
    show_default=True,
)
@click.option(
    "--commit/--no-commit",
    help="Commit the changes to Git.",
    default=True,
    show_default=True,
)
@click.option("--push/--no-push", help="Push the changes to remote.")
@click.option("--merge-request/--no-merge-request", help="Open a merge request.")
@click.option("--pull-request/--no-pull-request", help="Open a pull request.")
@click.option(
    "-u",
    "--upstream",
    metavar="BRANCH",
    help="Specify the upstream branch",
    default="master",
    show_default=True,
)
@click.option(
    "-r",
    "--remote",
    metavar="REMOTE",
    help="Specify the remote to push to",
    default="origin",
    show_default=True,
)
@click.option(
    "-C",
    "--cwd",
    metavar="DIR",
    type=click.Path(exists=True, file_okay=False),
    help="Change to directory DIR before performing any actions",
)
@click.option("--dry-run", "-n", is_flag=True, help="Just show what would be done.")
@click.argument("packages", nargs=-1)
@click.version_option(version=__version__)
def main(  # noqa: C901
    install: bool,
    commit: bool,
    push: bool,
    merge_request: bool,
    pull_request: bool,
    upstream: str,
    remote: str,
    dry_run: bool,
    packages: Tuple[str, ...],
    cwd: str = None,
) -> None:
    """Upgrade dependencies using Poetry."""
    if cwd is not None:
        os.chdir(cwd)

    if not git.is_clean():
        raise click.ClickException("Working tree is not clean")

    switch = commit or push or pull_request
    original_branch = git.current_branch()

    for package in poetry.show_outdated():
        if packages and package.name not in packages:
            continue

        show_package(package)

        if dry_run:
            continue

        branch = f"{program_name}/{package.name}-{package.new_version}"
        title = f"Upgrade to {package.name} {package.new_version}"
        description = (
            f"Upgrade {package.name} from {package.old_version}"
            f" to {package.new_version}"
        )
        message = f"{title}\n\n{description}\n"

        if switch:
            git.switch(branch, create=not git.branch_exists(branch), location=upstream)

        poetry.update(package.name, lock=not install)

        if not git.is_clean(["pyproject.toml", "poetry.lock"]) and commit:
            git.add(["pyproject.toml", "poetry.lock"])
            git.commit(message=message)

        if switch and git.resolve_branch(branch) == git.resolve_branch(upstream):
            click.echo(
                f"Skipping {package.name} {package.new_version}"
                " (Poetry refused upgrade)"
            )

            git.switch(original_branch)
            git.remove_branch(branch)

            continue

        if push:
            mr = git.MergeRequest(title, description) if merge_request else None
            git.push(remote, branch, merge_request=mr)

        if pull_request and not github.pull_request_exists(branch):
            github.create_pull_request(title, description)

    if original_branch != git.current_branch():
        git.switch(original_branch)
