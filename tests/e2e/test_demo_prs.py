"""End to end: real Demo PRs on GitHub, and what docs-guardian's workflows do with them.

Each scenario breaks the Guarded Project on purpose in a temporary clone, pushes it as
`demo/<scenario>-<run-id>`, and opens it as a draft PR into the branch under test
(`--e2e-base`, default `main`; it must already be pushed, because the workflows install
docs-guardian from the PR's own checkout). The PRs run in parallel; then every check's
result, the key log line of each red check and the Drift Report comment are asserted.
Every Demo PR is closed unmerged and its branch deleted afterwards, pass or fail.

Opt-in, slow (minutes) and outward-facing: `uv run pytest -m e2e`. It uses your `gh`
login. Plain `uv run pytest` and CI skip it. ADR 0004 explains why it opens real PRs.
"""

import json
import re
import secrets
import subprocess
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e

REPO = Path(__file__).resolve().parents[2]
# Every check a pull request gets. A check that is missing, renamed or new fails the
# comparison, so the suite cannot quietly fall behind the workflows.
CHECKS = (
    "tests (Python 3.11)",
    "tests (Python 3.14)",
    "ruff",
    "snippets",
    "notebooks",
    "drift",
    "markdownlint",
    "vale",
    "strict-build",
    "links",
)
DRIFT_MARKER = "<!-- docs-guardian:drift-report"
TIMEOUT = 20 * 60  # seconds, per wait for one commit's checks
POLL = 15
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def run(*args: str, cwd: Path = REPO) -> str:
    try:
        return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout
    except subprocess.CalledProcessError as error:
        raise AssertionError(f"{' '.join(args)} failed:\n{error.stderr}") from error


def gh_api(path: str):
    return json.loads(run("gh", "api", path))


@dataclass
class DemoPR:
    scenario: str
    branch: str
    clone: Path
    number: int = 0
    url: str = ""
    checks: dict = field(default_factory=dict)  # check name -> the check run, latest commit

    def head(self) -> str:
        return run("git", "rev-parse", "HEAD", cwd=self.clone).strip()


# --- Scenarios: each edits a fresh clone of the branch under test ---------------------


def replace(root: Path, paths: list[str], old: str, new: str) -> None:
    pattern = re.compile(rf"\b{re.escape(old)}\b")
    for path in paths:
        file = root / path
        text = file.read_text()
        assert pattern.search(text), f"{path} no longer holds {old!r}: update the scenario"
        file.write_text(pattern.sub(new, text))


def rename_fit_linear(root: Path) -> None:
    """Architecture §4: rename `fit_linear` to `fit` in the code and tests, not the Pages."""
    replace(
        root,
        [
            "tinyml/src/tinyml/__init__.py",
            "tinyml/src/tinyml/models.py",
            "tinyml/tests/test_tinyml.py",
        ],
        "fit_linear",
        "fit",
    )


def fix_the_docs(root: Path) -> None:
    """The follow-up push to the rename: the Pages catch up."""
    replace(
        root,
        [
            "tinyml/docs/quickstart.md",
            "tinyml/docs/tutorial.md",
            "tinyml/docs/notebooks/walkthrough.ipynb",
        ],
        "fit_linear",
        "fit",
    )


def break_the_docs(root: Path) -> None:
    """A house-style violation and a dead link to the site's own URL; no code change."""
    with (root / "tinyml/docs/index.md").open("a") as page:
        page.write(
            "\nFound a problem? Report it on Github, or read the "
            "[roadmap](https://willyowl.github.io/docs-guardian/missing/).\n"
        )


def harmless_change(root: Path) -> None:
    """Touches the source but not its API: nothing should fire."""
    with (root / "tinyml/src/tinyml/models.py").open("a") as module:
        module.write("\n\n# A change that alters no API.\n")


SCENARIOS: dict[str, tuple[str, Callable[[Path], None]]] = {
    "rename": ("rename fit_linear to fit, Pages untouched", rename_fit_linear),
    "docs-breakage": ("a house-style violation and a dead link", break_the_docs),
    "control": ("a change that alters no API", harmless_change),
}


# --- GitHub ---------------------------------------------------------------------------


def commit_and_push(pr: DemoPR, message: str) -> None:
    run("git", "commit", "-qam", message, cwd=pr.clone)
    run("git", "push", "-q", "origin", f"HEAD:refs/heads/{pr.branch}", cwd=pr.clone)


def wait_for_checks(slug: str, sha: str) -> dict:
    """Every check run on `sha`, by name, once all of them have completed."""
    deadline = time.monotonic() + TIMEOUT
    while True:
        latest = {}
        for check in sorted(
            gh_api(f"repos/{slug}/commits/{sha}/check-runs?per_page=100")["check_runs"],
            key=lambda check: check["id"],
        ):
            latest[check["name"]] = check
        pending = sorted(set(CHECKS) - latest.keys()) + sorted(
            name for name, check in latest.items() if check["status"] != "completed"
        )
        if not pending:
            return latest
        if time.monotonic() > deadline:
            pytest.fail(f"checks on {sha[:7]} still pending after {TIMEOUT // 60} min: {pending}")
        time.sleep(POLL)


def results(pr: DemoPR) -> dict[str, str]:
    return {name: check["conclusion"] for name, check in pr.checks.items()}


def expect(*red: str) -> dict[str, str]:
    return {name: "failure" if name in red else "success" for name in CHECKS}


def job_log(slug: str, pr: DemoPR, check: str) -> str:
    # For GitHub Actions a check run's id is its job's id.
    job = pr.checks[check]["id"]
    log = run("gh", "api", "--allow-escape-sequences", f"repos/{slug}/actions/jobs/{job}/logs")
    return ANSI.sub("", log)


def drift_reports(slug: str, pr: DemoPR) -> list[dict]:
    return [
        comment
        for comment in gh_api(f"repos/{slug}/issues/{pr.number}/comments?per_page=100")
        if comment["user"]["login"] == "github-actions[bot]"
        and comment["body"].startswith(DRIFT_MARKER)
    ]


@pytest.fixture(scope="module")
def slug() -> str:
    return run("gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner").strip()


@pytest.fixture(scope="module")
def demo(request, slug, tmp_path_factory) -> Iterator[dict[str, DemoPR]]:
    """Open every scenario's Demo PR, wait for all their checks, close them all after."""
    base = request.config.getoption("--e2e-base")
    remote = run("git", "remote", "get-url", "origin").strip()
    pushed = run("git", "ls-remote", "--heads", remote, base).split()
    if not pushed:
        pytest.fail(f"--e2e-base {base!r} is not on {remote}: push it first")
    local = subprocess.run(
        ["git", "rev-parse", "--verify", "-q", f"refs/heads/{base}"],
        cwd=REPO,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if local and local != pushed[0]:
        pytest.fail(f"local {base!r} is not the pushed one: push it first")

    run_id = secrets.token_hex(3)
    run(
        "gh", "label", "create", "e2e", "--repo", slug, "--force",
        "--color", "BFD4F2", "--description", "Demo PR opened by the e2e suite; never merged",
    )  # fmt: skip
    prs: dict[str, DemoPR] = {}
    try:
        for scenario, (title, edit) in SCENARIOS.items():
            pr = DemoPR(
                scenario, f"demo/{scenario}-{run_id}", tmp_path_factory.mktemp(scenario) / "repo"
            )
            run("git", "clone", "-q", "--depth", "1", "--branch", base, remote, str(pr.clone))
            edit(pr.clone)
            prs[scenario] = pr  # from here on, cleanup deletes the branch
            commit_and_push(pr, f"demo: {title}")
            pr.url = run(
                "gh", "pr", "create", "--repo", slug, "--draft", "--label", "e2e",
                "--base", base, "--head", pr.branch,
                "--title", f"demo: {title} (e2e run {run_id})",
                "--body", f"Demo PR opened by `tests/e2e/test_demo_prs.py` (run `{run_id}`) "
                f"to check how docs-guardian's checks respond. Never merged; closed by the suite.",
            ).strip()  # fmt: skip
            pr.number = int(pr.url.rsplit("/", 1)[1])
        for pr in prs.values():
            pr.checks = wait_for_checks(slug, pr.head())
        yield prs
    finally:
        failures = []
        for pr in prs.values():
            print(f"Demo PR {pr.scenario}: {pr.url or pr.branch}")
            try:
                if pr.number:
                    run("gh", "pr", "close", str(pr.number), "--repo", slug, "--delete-branch")
                else:
                    run("git", "push", "-q", "origin", "--delete", pr.branch, cwd=pr.clone)
            except AssertionError as error:
                failures.append(str(error))
        assert not failures, "cleanup failed:\n" + "\n".join(failures)


# --- The scenarios' expected outcomes -------------------------------------------------


def test_a_rename_turns_the_snippet_gates_red_and_posts_a_drift_report(demo, slug):
    pr = demo["rename"]
    assert results(pr) == expect("snippets", "notebooks")

    snippets = job_log(slug, pr, "snippets")
    missing = "ImportError: cannot import name 'fit_linear'"
    assert f"FAIL tinyml/docs/quickstart.md:8  {missing}" in snippets
    assert f"FAIL tinyml/docs/tutorial.md:39  {missing}" in snippets
    assert "4 Pages: 2 passed, 2 failed" in snippets
    notebooks = job_log(slug, pr, "notebooks")
    assert "FAILED tinyml/docs/notebooks/walkthrough.ipynb" in notebooks
    assert "cannot import name 'fit_linear'" in notebooks

    [report] = drift_reports(slug, pr)
    assert (
        "| `fit_linear` | removed | `notebooks/walkthrough.ipynb (cell 2, line 1)`, "
        "`notebooks/walkthrough.ipynb (cell 6, line 1)`, `quickstart.md:8`, `quickstart.md:14`, "
        "`tutorial.md:36`, `tutorial.md:39`, `tutorial.md:41` |"
    ) in report["body"]
    assert "**Not yet documented**: no Page Mentions `fit`." in report["body"]


def test_fixing_the_docs_turns_every_check_green_and_rewrites_the_report_in_place(demo, slug):
    pr = demo["rename"]
    [before] = drift_reports(slug, pr)
    fix_the_docs(pr.clone)
    commit_and_push(pr, "demo: the Pages catch up with the rename")
    pr.checks = wait_for_checks(slug, pr.head())
    assert results(pr) == expect()

    [after] = drift_reports(slug, pr)
    assert after["id"] == before["id"]
    assert "2 API Changes; no Drift." in after["body"]
    assert "| `fit_linear` | removed | none |" in after["body"]
    assert "Not yet documented" not in after["body"]


def test_broken_docs_turn_the_lint_gates_red_and_post_no_drift_report(demo, slug):
    pr = demo["docs-breakage"]
    assert results(pr) == expect("vale", "links")
    assert "Use 'GitHub' instead of 'Github'." in job_log(slug, pr, "vale")
    links = job_log(slug, pr, "links")
    assert "File not found" in links
    assert "Remaps: https://willyowl.github.io/docs-guardian/missing/ -->" in links
    assert "🚫 1 Error" in links  # only the planted link, not some unrelated one
    assert drift_reports(slug, pr) == []


def test_a_change_that_alters_no_api_keeps_every_check_green_and_quiet(demo, slug):
    pr = demo["control"]
    assert results(pr) == expect()
    assert drift_reports(slug, pr) == []
