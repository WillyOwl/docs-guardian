"""Independent regression expectations, outside the reviewed source tree."""
import subprocess
import sys

import pytest

from docs_guardian.snippets import extract_snippets, run_page


@pytest.mark.parametrize('markdown', [
    '- Example:\n\n    ```python\n    raise RuntimeError("broken nested Snippet")\n    ```\n',
    '> ```python\n> raise RuntimeError("broken nested Snippet")\n> ```\n',
], ids=['list', 'blockquote'])
def test_commonmark_nested_python_snippets_must_run(tmp_path, markdown):
    page = tmp_path / 'nested.md'
    page.write_text(markdown)
    print('Markdown source:\n' + markdown)
    print('extract_snippets:', extract_snippets(markdown))
    result = subprocess.run([sys.executable, '-m', 'docs_guardian.cli', 'snippets', str(tmp_path)],
                            capture_output=True, text=True)
    print(result.stdout, end='')
    print('CLI exit:', result.returncode)
    assert result.returncode == 1, 'Broken Python Snippet was silently passed'


def test_html_comments_do_not_contain_rendered_snippets(tmp_path):
    markdown = '<!--\n```python\nraise RuntimeError("hidden draft")\n```\n-->\n'
    page = tmp_path / 'comment.md'
    page.write_text(markdown)
    result = run_page(page)
    print('Markdown source:\n' + markdown)
    print('Result:', result)
    assert result.passed, 'Code inside an HTML comment is not a rendered Snippet'


def test_background_thread_timeout_must_fail_the_page(tmp_path):
    markdown = ('```python\nimport threading, time\n'
                'threading.Thread(target=lambda: time.sleep(60)).start()\n```\n')
    page = tmp_path / 'thread.md'
    page.write_text(markdown)
    print('Markdown source:\n' + markdown)
    result = subprocess.run([sys.executable, '-m', 'docs_guardian.cli', 'snippets', str(tmp_path),
                             '--timeout', '1'], capture_output=True, text=True, timeout=5)
    print(result.stdout, end='')
    print('CLI exit:', result.returncode)
    assert result.returncode == 1, 'A worker killed at its timeout was reported as passed'


def test_syntax_error_points_to_the_actual_page_line(tmp_path):
    markdown = '# Syntax\n\n```python\na = 1\nb = 2\nif True print(a)\n```\n'
    page = tmp_path / 'syntax.md'
    page.write_text(markdown)
    result = run_page(page)
    print('Markdown source:\n' + markdown)
    print('Result:', result)
    assert result.line == 6, 'SyntaxError points to the start of the Snippet, not the broken line'
