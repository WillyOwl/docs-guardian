"""The `docs-guardian` command line."""

import argparse
import os
import sys
from pathlib import Path

from docs_guardian.drift import DriftConfigError, drift_report
from docs_guardian.snippets import DEFAULT_TIMEOUT, PageResult, run_pages


def _plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def _show(path: Path) -> str:
    """A path relative to the working directory when it is inside it."""
    try:
        return os.path.relpath(path) if path.resolve().is_relative_to(Path.cwd()) else str(path)
    except ValueError:  # different drive on Windows
        return str(path)


def _report(result: PageResult) -> str:
    page = _show(result.page)
    if result.passed:
        extra = f", {result.skipped} skipped" if result.skipped else ""
        return f"PASS {page}  {_plural(result.ran, 'Snippet')}{extra}"
    location = f"{page}:{result.line}" if result.line else page
    not_run = f"  ({_plural(result.not_run, 'Snippet')} not run)" if result.not_run else ""
    return f"FAIL {location}  {result.error}{not_run}"


def _run_snippets(args: argparse.Namespace) -> int:
    """`docs-guardian snippets`: run every Page under the docs root and report.

    Args:
        args: Parsed arguments: `docs_root` and `timeout`.

    Returns:
        0 when every Page passes, 1 when any fails, 2 when there are no Pages.
    """
    root = Path(args.docs_root)
    if not root.is_dir() or not any(root.rglob("*.md")):
        print(f"docs-guardian: no Markdown Pages under {root}", file=sys.stderr)
        return 2
    results = run_pages(root, timeout=args.timeout)
    for result in results:
        print(_report(result))
    failed = sum(not r.passed for r in results)
    print(f"\n{_plural(len(results), 'Page')}: {len(results) - failed} passed, {failed} failed")
    return 1 if failed else 0


def _run_drift(args: argparse.Namespace) -> int:
    """`docs-guardian drift`: print the Drift Report, and write it to `--output` if given.

    Args:
        args: Parsed arguments: `base`, `source`, `docs` and `output`.

    Returns:
        0 whatever the report says: the drift check is Advisory (ADR 0001), and
        files the pull request leaves unreadable are listed, not fatal. 2 for a
        misconfigured run (unknown base, or a folder with nothing to check), so
        a mistyped path cannot pass as "No API Changes".
    """
    try:
        report = drift_report(args.base, Path(args.source), Path(args.docs))
    except DriftConfigError as error:
        print(f"docs-guardian: {error}", file=sys.stderr)
        return 2
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
    print(report, end="")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the `docs-guardian` command line.

    Args:
        argv: Arguments after the program name; defaults to `sys.argv[1:]`.

    Returns:
        The exit code for the chosen command.
    """
    parser = argparse.ArgumentParser(
        prog="docs-guardian", description="Catch documentation that no longer matches its code."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    snippets = commands.add_parser(
        "snippets",
        help="run every Snippet of every Markdown Page (a Gate)",
        description="Run each Markdown Page's python Snippets in order, one Page per process, "
        "each in an empty folder, with the Python running docs-guardian (so the Guarded "
        "Project must be installed in its environment). Exits 1 if any Page fails, 2 if "
        "there are no Pages.",
    )
    snippets.add_argument("docs_root", help="folder of Markdown Pages, searched recursively")
    snippets.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"seconds a Page may run (default: {DEFAULT_TIMEOUT:g})",
    )
    snippets.set_defaults(handler=_run_snippets)
    drift = commands.add_parser(
        "drift",
        help="report API Changes and the Pages that Mention them (Advisory)",
        description="Compare the public API under --source in this checkout (uncommitted "
        "edits included) with its merge base with --base, and list the Pages under --docs "
        "whose code Mentions what changed. Exits 0 whatever it finds: the drift check warns, "
        "it never fails the build. Exits 2 if --base or a folder is wrong.",
    )
    drift.add_argument("--base", required=True, help="branch to compare with, e.g. origin/main")
    drift.add_argument("--source", required=True, help="folder holding the Python packages")
    drift.add_argument("--docs", required=True, help="folder of Pages, searched recursively")
    drift.add_argument("--output", help="also write the report to this file")
    drift.set_defaults(handler=_run_drift)
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
