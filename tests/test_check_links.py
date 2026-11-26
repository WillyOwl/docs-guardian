"""The docs-lint `links` check (.github/scripts/check-links.sh), run on small built sites.

The sites are hand-written HTML shaped like MkDocs output, so these tests guard the
link-checking rules; the real tinyml build is checked by the `links` job itself.
They need the lychee binary: `$LYCHEE`, or `lychee` on PATH. CI's `links` job runs them.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / ".github/scripts/check-links.sh"
LYCHEE = os.environ.get("LYCHEE") or shutil.which("lychee")

needs_lychee = pytest.mark.skipif(not LYCHEE, reason="needs lychee ($LYCHEE or on PATH)")


def check(tmp_path: Path, links: str) -> subprocess.CompletedProcess:
    """Build a two-Page site whose home Page holds `links`, and check it."""
    site = Path(tempfile.mkdtemp(dir=tmp_path)) / "site"  # one fresh site per call
    (site / "quickstart").mkdir(parents=True)
    (site / "index.html").write_text(f"<html><body><h1>Home</h1>{links}</body></html>")
    (site / "quickstart/index.html").write_text(
        '<html><body><h1 id="quickstart">Quickstart</h1><h2 id="install">Install</h2></body></html>'
    )
    return subprocess.run(
        ["bash", str(SCRIPT), str(site)],
        env={**os.environ, "LYCHEE": LYCHEE},
        capture_output=True,
        text=True,
        timeout=120,
    )


@needs_lychee
def test_a_relative_link_to_a_missing_page_fails_and_one_to_a_page_passes(tmp_path):
    assert check(tmp_path, '<a href="quickstart/">ok</a>').returncode == 0
    broken = check(tmp_path, '<a href="missing/">gone</a>')
    assert broken.returncode != 0
    assert "missing" in broken.stdout + broken.stderr


SITE_URL = "https://willyowl.github.io/docs-guardian/"


@needs_lychee
def test_a_link_to_the_sites_own_url_is_checked_against_the_local_build(tmp_path):
    # Review round 1, Spec 1. Checked locally, so a Page this PR adds passes before deploy.
    assert check(tmp_path, f'<a href="{SITE_URL}quickstart/">ok</a>').returncode == 0
    broken = check(tmp_path, f'<a href="{SITE_URL}missing-page/">gone</a>')
    assert broken.returncode != 0
    assert "missing-page" in broken.stdout + broken.stderr


@needs_lychee
def test_a_link_to_a_missing_heading_fails_and_one_to_a_heading_passes(tmp_path):
    # Review round 1, Spec 2: the strict build checks anchors in Markdown Pages
    # only, so a notebook's `#heading` links are lychee's to check.
    ok = '<h2 id="fit">Fit</h2><a href="#fit">here</a> <a href="quickstart/#install">there</a>'
    assert check(tmp_path, ok).returncode == 0
    for link in ("#no-such-heading", "quickstart/#no-such-heading"):
        broken = check(tmp_path, f'<a href="{link}">gone</a>')
        assert broken.returncode != 0, link
        assert "no-such-heading" in broken.stdout + broken.stderr


def test_ci_checks_the_built_site_with_this_script_and_runs_these_tests():
    links_job = (REPO / ".github/workflows/docs-lint.yml").read_text().split("\n  links:")[1]
    assert "bash .github/scripts/check-links.sh tinyml/site" in links_job
    assert "pytest tests/test_check_links.py" in links_job
