"""Tests for update module."""
from poetry_up import poetry, update


def test_actions_are_required_by_default(package: poetry.Package) -> None:
    """It returns True by default."""
    options = update.Options(
        latest=True,
        install=True,
        commit=True,
        push=False,
        merge_request=False,
        pull_request=False,
        upstream="master",
        remote="origin",
        dry_run=False,
        packages=(),
    )
    updater = update.PackageUpdater(package, options, "master")
    assert update.Action(updater).required
