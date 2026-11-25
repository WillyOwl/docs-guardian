"""The drift-check workflow's posting script, run against a stub `gh`."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / ".github/scripts/post-drift-report.sh"

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash")

# Logs every call; `GH_MODE` picks how the comment lookup and the write respond.
STUB = f"""#!{sys.executable}
import json, os, sys
args = sys.argv[1:]
with open(os.environ["GH_CALLS"], "a") as log:
    log.write(json.dumps(args) + "\\n")
mode = os.environ["GH_MODE"]
if "-X" not in args:  # the lookup of earlier comments
    if mode == "lookup-fails":
        sys.exit("gh: HTTP 503 Service Unavailable")
    ids = {{"existing": 1, "many-existing": 100_000}}.get(mode, 0)
    sys.stdout.write("".join(f"{{1000 + i}}\\n" for i in range(ids)))
elif mode == "write-forbidden":
    sys.exit("gh: Resource not accessible by integration (HTTP 403)")
"""


def post(tmp_path, mode: str, changes: int = 1) -> tuple[subprocess.CompletedProcess, list]:
    """Run the script on a report with `changes` API Changes; return the run and gh calls."""
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin/gh").write_text(STUB)
    (tmp_path / "bin/gh").chmod(0o755)
    report = tmp_path / "drift-report.md"
    report.write_text(
        f"<!-- docs-guardian:drift-report changes={changes} drift-pages=0 -->\n### Drift Report\n"
    )
    env = {
        **os.environ,
        "PATH": f"{tmp_path / 'bin'}{os.pathsep}{os.environ['PATH']}",
        "GH_MODE": mode,
        "GH_CALLS": str(tmp_path / "calls.jsonl"),
        "GITHUB_REPOSITORY": "owner/repo",
        "PR": "7",
        "GITHUB_RUN_ID": "1",
    }
    run = subprocess.run(
        ["bash", str(SCRIPT), str(report)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    calls = [json.loads(line) for line in (tmp_path / "calls.jsonl").read_text().splitlines()]
    return run, [(c[c.index("-X") + 1], c[c.index("-X") + 2]) for c in calls if "-X" in c]


@pytest.mark.parametrize(
    ("mode", "changes", "writes"),
    [
        ("none", 0, []),
        ("none", 1, [("POST", "repos/owner/repo/issues/7/comments")]),
        ("existing", 1, [("PATCH", "repos/owner/repo/issues/comments/1000")]),
        ("existing", 0, [("PATCH", "repos/owner/repo/issues/comments/1000")]),
        ("many-existing", 1, [("PATCH", "repos/owner/repo/issues/comments/1000")]),
    ],
    ids=["nothing-to-post", "first-report", "rewrite", "rewrite-to-clear", "many-matches"],
)
def test_posts_a_first_report_and_rewrites_the_earlier_one(tmp_path, mode, changes, writes):
    run, made = post(tmp_path, mode, changes)
    assert run.returncode == 0, run.stderr
    assert made == writes
    assert "::warning::" not in run.stdout


@pytest.mark.parametrize(
    ("mode", "says"),
    [
        ("lookup-fails", "HTTP 503"),  # review round 2: this one used to fail the step
        ("write-forbidden", "HTTP 403"),
    ],
)
def test_a_github_api_failure_only_warns(tmp_path, mode, says):
    run, _ = post(tmp_path, mode)
    assert run.returncode == 0, run.stderr  # Advisory (ADR 0001)
    [warning] = [line for line in run.stdout.splitlines() if line.startswith("::warning::")]
    assert says in warning and "job summary" in warning


def test_the_workflow_runs_this_script():
    workflow = (REPO / ".github/workflows/drift-check.yml").read_text()
    assert "bash .github/scripts/post-drift-report.sh drift-report.md" in workflow
