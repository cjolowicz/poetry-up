"""Command-line interface."""
import os
from typing import Tuple

import click

from . import __version__, update


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

    options = update.Options(
        install,
        commit,
        push,
        merge_request,
        pull_request,
        upstream,
        remote,
        dry_run,
        packages,
    )
    updater = update.Updater(options)
    updater.run()
