from docs_guardian.drift import ApiChange, ChangeKind, Mention, render_report
changes = [
    ApiChange("fit", ChangeKind.CHANGED, ("(x: int | str)",), ("(x: int | str, sep='`')", "(y)")),
    ApiChange("old", ChangeKind.REMOVED, ("()",), None),
]
mentions = {"fit": [Mention("quick|start.md", 2), Mention("walk.ipynb", 1, 3)], "old": []}
print(render_report(changes, mentions, "main", "1234567abc"), end="")
