"""The public part of a strategy script: what static/assets/previews may show.

The factory cuts the paid scripts' previews 50 lines into their first tree and ends them with a
note (checked against all 2,755 of them); it left the free ones whole. publish.py cuts every
preview with this, and the tests check every file in static/assets/previews against it.
"""
PREVIEW_TREE_LINES = 50
PREVIEW_TAIL = "\n\t...\nThe rest of this Pine script is part of the paid version. Visit the website for more info.\n"


def cut_preview(script: str) -> str:
    """The public part of a script; a preview that is already cut comes back unchanged."""
    if script.endswith(PREVIEW_TAIL):
        return script
    lines = script.replace("\r\n", "\n").split("\n")
    start = next((i for i, line in enumerate(lines) if line.startswith("decision_tree_")), None)
    if start is None:
        raise ValueError("no decision_tree_ function: not a strategy script")
    return "\n".join(lines[:start + PREVIEW_TREE_LINES]) + "\n" + PREVIEW_TAIL
