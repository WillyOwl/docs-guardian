"""Adversarial CLI scenarios for `docs-guardian drift`. Prints [DEBUG-h2] per scenario."""
import os, shutil, subprocess, sys, tempfile
from pathlib import Path

DG = shutil.which("docs-guardian")

def sh(cwd, *a):
    subprocess.run(a, cwd=cwd, check=True, capture_output=True)

def repo(tmp):
    sh(tmp, "git", "init", "-q", "-b", "main"); sh(tmp, "git", "config", "user.email", "t@e.x"); sh(tmp, "git", "config", "user.name", "t")
    (tmp / "src/pkg").mkdir(parents=True)
    (tmp / "src/pkg/__init__.py").write_text("def fit(X, y): ...\ndef evaluate(y) -> float: ...\n")
    (tmp / "docs").mkdir()
    (tmp / "docs/q.md").write_text("```python\nfit(X, y)\nevaluate(y)\n```\n")
    sh(tmp, "git", "add", "."); sh(tmp, "git", "commit", "-qm", "base"); sh(tmp, "git", "switch", "-qc", "feat")

def run(cwd, *args):
    p = subprocess.run([DG, "drift", *args], cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr

def change_fit(t):  # one changed API, Mentioned on q.md:2
    (t / "src/pkg/__init__.py").write_text("def fit(X, y, w=None): ...\ndef evaluate(y) -> float: ...\n")

SCENARIOS = {}
def scenario(f): SCENARIOS[f.__name__] = f; return f

@scenario
def baseline(t):
    change_fit(t); return run(t, "--base", "main", "--source", "src", "--docs", "docs"), (0, "changes=1 drift-pages=1")
@scenario
def source_is_repo_root(t):
    change_fit(t); return run(t, "--base", "main", "--source", ".", "--docs", "docs"), (0, "changes=1 drift-pages=1")
@scenario
def run_from_subdirectory(t):
    change_fit(t); return run(t / "docs", "--base", "main", "--source", "../src", "--docs", "."), (0, "changes=1 drift-pages=1")
@scenario
def absolute_paths(t):
    change_fit(t); return run(Path("/"), "--base", "main", "--source", str(t / "src"), "--docs", str(t / "docs")), (0, "changes=1 drift-pages=1")
@scenario
def trailing_slashes(t):
    change_fit(t); return run(t, "--base", "main", "--source", "src/", "--docs", "docs/"), (0, "changes=1 drift-pages=1")
@scenario
def base_is_a_sha(t):
    change_fit(t); sha = subprocess.run(["git", "rev-parse", "main"], cwd=t, capture_output=True, text=True).stdout.strip()
    return run(t, "--base", sha, "--source", "src", "--docs", "docs"), (0, "changes=1 drift-pages=1")
@scenario
def detached_head(t):
    change_fit(t); sh(t, "git", "commit", "-qam", "c"); sh(t, "git", "switch", "-q", "--detach")
    return run(t, "--base", "main", "--source", "src", "--docs", "docs"), (0, "changes=1 drift-pages=1")
@scenario
def new_package_not_at_base(t):
    (t / "src/newpkg").mkdir(); (t / "src/newpkg/__init__.py").write_text("def brand_new(): ...\n")
    return run(t, "--base", "main", "--source", "src", "--docs", "docs"), (0, "changes=1 drift-pages=0")
@scenario
def source_dir_not_at_base(t):
    (t / "lib/pkg2").mkdir(parents=True); (t / "lib/pkg2/__init__.py").write_text("def other(): ...\n")
    return run(t, "--base", "main", "--source", "lib", "--docs", "docs"), (0, "changes=1 drift-pages=0")
@scenario
def module_deleted(t):
    (t / "src/pkg/__init__.py").unlink()
    (t / "src/pkg/other.py").write_text("def unrelated(): ...\n")
    return run(t, "--base", "main", "--source", "src", "--docs", "docs"), (0, "changes=3 drift-pages=1")
@scenario
def crlf_page(t):
    change_fit(t); (t / "docs/q.md").write_bytes(b"# T\r\n\r\nUse `fit` here.\r\n\r\n```python\r\nfit(X, y)\r\n```\r\n")
    return run(t, "--base", "main", "--source", "src", "--docs", "docs"), (0, "`q.md:3`, `q.md:6`")
@scenario
def bom_page(t):
    change_fit(t); (t / "docs/q.md").write_bytes("﻿Use `fit`.\n\n```python\nfit(X, y)\n```\n".encode())
    return run(t, "--base", "main", "--source", "src", "--docs", "docs"), (0, "`q.md:1`, `q.md:4`")
@scenario
def symlinked_module(t):
    change_fit(t); (t / "src/pkg/alias.py").symlink_to(t / "src/pkg/__init__.py")
    sh(t, "git", "add", "-A"); sh(t, "git", "commit", "-qm", "link"); sh(t, "git", "branch", "-f", "main")
    return run(t, "--base", "main", "--source", "src", "--docs", "docs"), (0, "changes=0")
@scenario
def ignored_build_copy(t):
    (t / ".gitignore").write_text("build/\n"); (t / "src/pkg/build").mkdir(); (t / "src/pkg/build/copy.py").write_text("def stale_copy(): ...\n")
    return run(t, "--base", "main", "--source", "src", "--docs", "docs"), (0, "changes=0")
@scenario
def output_into_missing_folder(t):
    change_fit(t); return run(t, "--base", "main", "--source", "src", "--docs", "docs", "--output", "no/such/dir/r.md"), (2, "")
@scenario
def latin1_coding_cookie(t):
    (t / "src/pkg/l1.py").write_bytes(b"# -*- coding: latin-1 -*-\ndef caf\xe9(): ...\ndef plain(): ...\n")
    return run(t, "--base", "main", "--source", "src", "--docs", "docs"), (0, "no Page Mentions `café`, `plain`.")
@scenario
def docs_inside_source(t):
    change_fit(t); shutil.move(t / "docs", t / "src/docs")
    return run(t, "--base", "main", "--source", "src", "--docs", "src/docs"), (0, "changes=1 drift-pages=1")
@scenario
def not_a_git_repo(t):
    shutil.rmtree(t / ".git"); return run(t, "--base", "main", "--source", "src", "--docs", "docs"), (2, "")
@scenario
def page_with_only_skipped_and_prose(t):
    change_fit(t); (t / "docs/q.md").write_text("<!-- docs-guardian: skip -->\n```python\nfit(X)\n```\n")
    return run(t, "--base", "main", "--source", "src", "--docs", "docs"), (0, "`q.md:3`")

only = sys.argv[1:]
for name, f in SCENARIOS.items():
    if only and name not in only: continue
    with tempfile.TemporaryDirectory() as d:
        t = Path(d); repo(t)
        (code, out, err), (want_code, want_text) = f(t)
        ok = code == want_code and want_text in out and "Traceback" not in err
        print(f"[DEBUG-h2] {'ok  ' if ok else 'RED '} {name}: exit {code} (want {want_code})"
              + ("" if ok else f"\n    want {want_text!r}\n    out: {out.strip()[:600]!r}\n    err: {err.strip()[-600:]!r}"))
