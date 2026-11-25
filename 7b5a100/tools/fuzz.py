"""Property loops over the drift check. Prints [DEBUG-h1] lines for every counterexample."""
import json, random, sys, tempfile
from pathlib import Path
from markdown_it import MarkdownIt
from docs_guardian.drift import find_mentions, _code

N = int(sys.argv[1]) if len(sys.argv) > 1 else 300
rng = random.Random(3)
fails = {"lines": 0, "cells": 0, "notebook": 0}

# 1. Every inline code span is reported on the line where it starts.
def page(rng):
    lines, expect, k = [], {}, 0
    for _ in range(rng.randint(1, 6)):
        prefix = rng.choice(["", "- ", "> ", "1. ", "  ", "# "])
        heading = prefix == "# "
        for j in range(1 if heading else rng.randint(1, 3)):
            words = []
            for _ in range(rng.randint(0, 4)):
                if rng.random() < 0.4:
                    k += 1; name = f"api{k}"
                    expect[name] = len(lines) + 1 + sum(w.count("\n") for w in words)
                    words.append(rng.choice([f"`{name}`", f"`` {name}` ``", f"[`{name}`](x)", f"*`{name}`*"] + ([] if heading else [f"`{name}\nzz`"])))
                else:
                    words.append(rng.choice(["api9999 prose", "x", "&amp;", "**s**", "a_b"]))
            text = " ".join(words) or "w"
            for t_i, t in enumerate(text.split("\n")):
                lines.append((prefix if (j == 0 and t_i == 0) or prefix in ("> ",) else " " * len(prefix)) + t)
        lines.append("")
    return "\n".join(lines) + "\n", expect

with tempfile.TemporaryDirectory() as d:
    for i in range(N):
        text, expect = page(rng)
        (Path(d) / "p.md").write_text(text)
        found = find_mentions(Path(d), list(expect))
        for name, line in expect.items():
            got = [m.line for m in found[name]]
            if got != [line]:
                fails["lines"] += 1
                if fails["lines"] <= 3:
                    print(f"[DEBUG-h1] lines: {name} expected {line} got {got}\n{text}")

# 2. _code round-trips any text through a GFM table cell.
md = MarkdownIt("commonmark").enable("table")
alphabet = ["a", "|", "`", " ", "\\", "*", "<", "&", "→", "_"]
for i in range(N * 3):
    s = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 8)))
    if not s.strip() or s != s.strip(" "):
        continue
    tokens = md.parse(f"| h | h2 |\n| --- | --- |\n| {_code(s)} | end |\n")
    cells = [t for t in tokens if t.type == "inline"][2:]
    kids = cells[0].children if cells else []
    ok = len(cells) == 2 and len(kids) == 1 and kids[0].type == "code_inline" and kids[0].content == s
    if not ok:
        fails["cells"] += 1
        if fails["cells"] <= 5:
            print(f"[DEBUG-h1] cells: {s!r} -> {_code(s)!r} -> {[(k.type, k.content) for k in kids]} ncells={len(cells)}")

# 3. No JSON value read as a notebook raises.
def value(depth=0):
    r = rng.random()
    if depth > 3 or r < 0.3: return rng.choice([None, 1, "s", True, 1.5, "code", "x = 1\n"])
    if r < 0.6: return [value(depth + 1) for _ in range(rng.randint(0, 3))]
    keys = ["cells", "cell_type", "source", "metadata", "x"]
    return {rng.choice(keys): value(depth + 1) for _ in range(rng.randint(0, 3))}
with tempfile.TemporaryDirectory() as d:
    for i in range(N * 3):
        v = value()
        if rng.random() < 0.5: v = {"cells": [{"cell_type": "code", "source": value(2)} for _ in range(2)]}
        (Path(d) / "n.ipynb").write_text(json.dumps(v))
        try:
            find_mentions(Path(d), ["x"], unreadable=[])
        except Exception as e:
            fails["notebook"] += 1
            if fails["notebook"] <= 3: print(f"[DEBUG-h1] notebook: {v!r} -> {type(e).__name__}: {e}")
print("[DEBUG-h1] failures:", fails)
