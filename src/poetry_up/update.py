"""Update module."""
from dataclasses import dataclass
from typing import Tuple

import click

from . import git, github, poetry


program_name = "poetry-up"


@dataclass
class Options:
    """Options for the update operation."""

    install: bool
    commit: bool
    push: bool
    merge_request: bool
    pull_request: bool
    upstream: str
    remote: str
    dry_run: bool
    packages: Tuple[str, ...]


class Action:
    """Base class for actions."""

    def __init__(self, updater: "PackageUpdater") -> None:
        """Constructor."""
        self.updater = updater

    @property
    def required(self) -> bool:
        """Return True if the action needs to run."""
        return True

    def __call__(self) -> None:
        """Run the action."""


class Switch(Action):
    """Switch to the update branch."""

    @property
    def required(self) -> bool:
        """Return True if the action needs to run."""
        return (
            self.updater.options.commit
            or self.updater.options.push
            or self.updater.options.pull_request
        )

    def __call__(self) -> None:
        """Run the action."""
        git.switch(
            self.updater.branch,
            create=not git.branch_exists(self.updater.branch),
            location=self.updater.options.upstream,
        )


class Update(Action):
    """Update the package using Poetry."""

    def __call__(self) -> None:
        """Run the action."""
        poetry.update(self.updater.package, lock=not self.updater.options.install)


class Commit(Action):
    """Create a Git commit for the update."""

    @property
    def required(self) -> bool:
        """Return True if the action needs to run."""
        return self.updater.options.commit and not git.is_clean(
            ["pyproject.toml", "poetry.lock"]
        )

    def __call__(self) -> None:
        """Run the action."""
        git.add(["pyproject.toml", "poetry.lock"])
        git.commit(message=f"{self.updater.title}\n")


class Rollback(Action):
    """Rollback an attempted package update."""

    @property
    def required(self) -> bool:
        """Return True if the action needs to run."""
        return self.updater.actions.switch.required and (
            git.resolve_branch(self.updater.branch)
            == git.resolve_branch(self.updater.options.upstream)
        )

    def __call__(self) -> None:
        """Run the action."""
        click.echo(
            f"Skipping {self.updater.package.name} {self.updater.package.new_version}"
            " (Poetry refused upgrade)"
        )

        git.switch(self.updater.original_branch)
        git.remove_branch(self.updater.branch)


class Push(Action):
    """Push the update branch to the remote repository."""

    @property
    def required(self) -> bool:
        """Return True if the action needs to run."""
        return self.updater.options.push

    def __call__(self) -> None:
        """Run the action."""
        merge_request = (
            git.MergeRequest(self.updater.title, self.updater.description)
            if self.updater.options.merge_request
            else None
        )
        git.push(
            self.updater.options.remote,
            self.updater.branch,
            merge_request=merge_request,
        )


class PullRequest(Action):
    """Open a pull request for the update branch."""

    @property
    def required(self) -> bool:
        """Return True if the action needs to run."""
        return self.updater.options.pull_request and not github.pull_request_exists(
            self.updater.branch
        )

    def __call__(self) -> None:
        """Run the action."""
        github.create_pull_request(self.updater.title, self.updater.description)


@dataclass
class Actions:
    """Actions for a package update."""

    switch: Switch
    update: Update
    commit: Commit
    rollback: Rollback
    push: Push
    pull_request: PullRequest

    @classmethod
    def create(cls, updater: "PackageUpdater") -> "Actions":
        """Create the package update actions."""
        return cls(
            Switch(updater),
            Update(updater),
            Commit(updater),
            Rollback(updater),
            Push(updater),
            PullRequest(updater),
        )


class PackageUpdater:
    """Update a package."""

    def __init__(
        self, package: poetry.Package, options: Options, original_branch: str
    ) -> None:
        """Constructor."""
        self.package = package
        self.options = options
        self.original_branch = original_branch

        self.branch = f"{program_name}/{package.name}-{package.new_version}"
        self.title = (
            f"Bump {package.name} from {package.old_version} to {package.new_version}"
        )
        self.description = self.title

        self.actions = Actions.create(self)

    @property
    def required(self) -> bool:
        """Return True if the package needs to be updated."""
        return not self.options.packages or self.package.name in self.options.packages

    def run(self) -> None:
        """Run the package update."""
        if self.actions.switch.required:
            self.actions.switch()

        self.actions.update()

        if self.actions.commit.required:
            self.actions.commit()

        if self.actions.rollback.required:
            self.actions.rollback()
            return

        if self.actions.push.required:
            self.actions.push()

        if self.actions.pull_request.required:
            self.actions.pull_request()

    def show(self) -> None:
        """Print information about the package update."""
        message = "{}: {} → {}".format(
            click.style(self.package.name, fg="bright_green"),
            click.style(self.package.old_version, fg="blue"),
            click.style(
                self.package.new_version,
                fg="red" if self.package.compatible else "yellow",
            ),
        )
        click.echo(message)


class Updater:
    """Update packages."""

    def __init__(self, options: Options) -> None:
        """Constructor."""
        self.options = options

    def run(self) -> None:
        """Run the package updates."""
        if not git.is_clean():
            raise click.ClickException("Working tree is not clean")

        original_branch = git.current_branch()

        for package in poetry.show_outdated():
            updater = PackageUpdater(package, self.options, original_branch)
            if updater.required:
                updater.show()
                if not self.options.dry_run:
                    updater.run()

        if original_branch != git.current_branch():
            git.switch(original_branch)
