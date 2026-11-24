"""Run every ```python Snippet of each given Page, in order, in one namespace per Page.

Each Page's Snippets run with the Page's own folder as the working directory,
because Snippets use paths relative to their Page.
"""

import contextlib
import os
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^```python\n(.*?)^```", re.S | re.M)

failed = 0
for arg in sys.argv[1:]:
    page = Path(arg).resolve()
    namespace: dict = {}
    with contextlib.chdir(page.parent):
        for i, src in enumerate(FENCE.findall(page.read_text()), 1):
            print(f"── {page.name}, Snippet {i} " + "─" * 30)
            print("\n".join(">>> " + line for line in src.rstrip().splitlines()))
            try:
                exec(compile(src, f"{page.name}#{i}", "exec"), namespace)
                print("\033[32mok\033[0m")
            except Exception as exc:  # noqa: BLE001
                failed += 1
                print(f"\033[31mFAILED: {exc!r}\033[0m")
            print()
print(f"\033[1m{'all Snippets ran' if not failed else f'{failed} Snippet(s) failed'}\033[0m")
sys.exit(1 if failed else 0)
