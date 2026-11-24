"""Runs one Page's Snippets in this process: `python -m docs_guardian._worker <events-file>`.

Reads `{"page": ..., "snippets": [[line, code], ...]}` from stdin and runs the
Snippets in order, in one shared namespace. Progress goes to the events file,
one JSON object per line, because Snippets are free to print to stdout:

- `{"started": i}` before Snippet `i` runs;
- `{"failed": i, "line": n, "error": "Type: message"}` if it raises;
- `{"done": true}` once every Snippet has run. Without it, the runner treats
  the Page as crashed, so a process that dies silently never passes.
"""

import json
import sys
import traceback


def main(events_path: str) -> None:
    request = json.load(sys.stdin)
    page = request["page"]
    namespace: dict = {"__name__": "__main__"}
    with open(events_path, "a") as events:

        def emit(event: dict) -> None:
            events.write(json.dumps(event) + "\n")
            events.flush()

        for i, (line, code) in enumerate(request["snippets"]):
            emit({"started": i})
            # Pad so compiled line numbers are line numbers in the Page itself.
            source = "\n" * (line - 1) + code
            try:
                exec(compile(source, page, "exec"), namespace)
            except BaseException as exc:  # noqa: BLE001 - a Snippet may raise anything
                failing_line, error = _locate(exc, page, line)
                emit({"failed": i, "line": failing_line, "error": error})
                return
        emit({"done": True})


def _locate(exc: BaseException, page: str, snippet_line: int) -> tuple[int, str]:
    """Return the Page line an exception points at, and how to report it.

    A SyntaxError in the Snippet itself is raised while compiling, before any
    Page frame exists, so its own position is the answer. Anything else is
    found through the deepest traceback frame that belongs to the Page.
    """
    name = type(exc).__name__
    if isinstance(exc, SyntaxError) and exc.filename == page and exc.lineno:
        return exc.lineno, f"{name}: {exc.msg}"
    frames = [f for f in traceback.extract_tb(exc.__traceback__) if f.filename == page]
    line = frames[-1].lineno if frames and frames[-1].lineno else snippet_line
    return line, f"{name}: {exc}" if str(exc) else name


if __name__ == "__main__":
    main(sys.argv[1])
