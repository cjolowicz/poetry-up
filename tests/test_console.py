"""Test cases for the console module."""
from pathlib import Path
from typing import Iterator, List

from _pytest.monkeypatch import MonkeyPatch
from click.testing import CliRunner
import pytest

from poetry_up import console, git, poetry


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


@pytest.fixture
def stub_poetry_show_outdated(monkeypatch: MonkeyPatch) -> None:
    """Stub for poetry.show_outdated."""

    def stub() -> Iterator[poetry.Package]:
        yield poetry.Package("marshmallow", "3.0.0", "3.5.1")

    monkeypatch.setattr("poetry_up.poetry.show_outdated", stub)


@pytest.fixture
def stub_poetry_update(
    monkeypatch: MonkeyPatch, shared_datadir: Path, repository: Path
) -> None:
    """Stub for poetry.update."""

    def stub(package: poetry.Package, lock: bool = False, latest: bool = False) -> None:
        if package.name == "marshmallow":
            source = shared_datadir / "poetry.lock.new"
            destination = Path("poetry.lock")
            destination.write_text(source.read_text())

    monkeypatch.setattr("poetry_up.poetry.update", stub)


@pytest.fixture
def stub_poetry_update_noop(monkeypatch: MonkeyPatch) -> None:
    """Stub for poetry.update which does nothing."""

    def stub(package: poetry.Package, lock: bool = False, latest: bool = False) -> None:
        pass

    monkeypatch.setattr("poetry_up.poetry.update", stub)


@pytest.fixture
def stub_git_push(monkeypatch: MonkeyPatch) -> None:
    """Stub for git.push."""
    from poetry_up.git import push, MergeRequest

    def stub(remote: str, branch: str, merge_request: MergeRequest = None) -> None:
        push(remote, branch)

    monkeypatch.setattr("poetry_up.git.push", stub)


@pytest.fixture
def stub_pull_request_exists(monkeypatch: MonkeyPatch) -> None:
    """Stub for github.pull_request_exists."""
    monkeypatch.setattr("poetry_up.github.pull_request_exists", lambda branch: False)


@pytest.fixture
def stub_create_pull_request(monkeypatch: MonkeyPatch) -> None:
    """Stub for github.create_pull_request."""
    monkeypatch.setattr("poetry_up.github.create_pull_request", lambda *args: None)


class TestMain:
    """Tests for main."""

    def test_it_succeeds_with_dry_run(
        self, runner: CliRunner, repository: Path
    ) -> None:
        """It exits with a status code of zero when passed --dry-run."""
        result = runner.invoke(console.main, ["--dry-run"])
        assert result.exit_code == 0

    @pytest.mark.parametrize(
        "options",
        [
            [],
            ["--cwd=."],
            ["--no-install"],
            ["--no-commit"],
            ["--push"],
            ["--push", "--pull-request"],
            ["--push", "--merge-request"],
            ["marshmallow"],
            ["another-package"],
        ],
    )
    def test_it_succeeds(
        self,
        runner: CliRunner,
        repository: Path,
        options: List[str],
        stub_poetry_show_outdated: None,
        stub_poetry_update: None,
        stub_git_push: None,
        stub_pull_request_exists: None,
        stub_create_pull_request: None,
    ) -> None:
        """It exits with a status code of zero."""
        result = runner.invoke(console.main, options)
        assert result.exit_code == 0

    def test_it_fails_on_dirty_worktree(
        self, runner: CliRunner, repository: Path
    ) -> None:
        """It fails if the working tree is not clean."""
        pyproject_toml = Path("pyproject.toml")
        with pyproject_toml.open(mode="a") as io:
            io.write("\n")

        result = runner.invoke(console.main)
        assert result.exit_code == 1

    def test_it_creates_branch(
        self,
        runner: CliRunner,
        repository: Path,
        stub_poetry_show_outdated: None,
        stub_poetry_update: None,
    ) -> None:
        """It creates a branch for the upgrade."""
        runner.invoke(console.main, catch_exceptions=False)
        assert git.branch_exists("poetry-up/marshmallow-3.5.1")

    def test_it_removes_branch_on_refused_upgrade(
        self,
        runner: CliRunner,
        repository: Path,
        stub_poetry_show_outdated: None,
        stub_poetry_update_noop: None,
    ) -> None:
        """It removes the branch if the upgrade was refused."""
        runner.invoke(console.main, catch_exceptions=False)
        assert not git.branch_exists("poetry-up/marshmallow-3.5.1")
