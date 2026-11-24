"""Independent behavior checks; never installed into the PR source tree."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from docs_guardian.snippets import run_page


@pytest.mark.parametrize('stream', ['stdout', 'stderr'])
def test_valid_snippet_can_write_binary_output(tmp_path, stream):
    page = tmp_path / 'binary.md'
    page.write_text(f'```python\nimport sys\nsys.{stream}.buffer.write(bytes([255]))\n```\n')
    print('Snippet: import sys; sys.' + stream + '.buffer.write(bytes([255]))')
    result = run_page(page)
    print('Page result:', result)
    assert result.passed, 'A valid Snippet with binary output must pass'


def test_page_timeout_terminates_descendant_process(tmp_path):
    page = tmp_path / 'child.md'
    pid_path = tmp_path / 'child.pid'
    marker = tmp_path / 'ran_after_timeout'
    child_code = (
        'import os, time; from pathlib import Path; '
        f'Path({str(pid_path)!r}).write_text(str(os.getpid())); '
        f'time.sleep(1.5); Path({str(marker)!r}).write_text("still running"); '
        'time.sleep(30)'
    )
    page.write_text(
        '```python\nimport subprocess, sys, time\n'
        f'subprocess.Popen([sys.executable, "-c", {child_code!r}])\n'
        'time.sleep(30)\n```\n'
    )
    child_pid = None
    try:
        begin = time.monotonic()
        result = run_page(page, timeout=0.5)
        elapsed = time.monotonic() - begin
        if pid_path.exists():
            child_pid = int(pid_path.read_text())
        print('Page result:', result)
        print(f'run_page returned after {elapsed:.2f}s; configured timeout: 0.5s')
        assert result.error == 'Timeout: still running after 0.5s'
        assert child_pid is not None, 'Child process must have started for this check'
        deadline = begin + 2.5
        while time.monotonic() < deadline and not marker.exists():
            time.sleep(0.05)
        print('Descendant executed after Page timeout:', marker.exists())
        assert not marker.exists(), 'Descendant continued executing after the Page timed out'
    finally:
        if child_pid is not None:
            try:
                os.kill(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
