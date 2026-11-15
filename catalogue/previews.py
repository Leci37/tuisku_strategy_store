"""The public part of a strategy script: what static/assets/previews may show.

The factory cuts the paid scripts' previews 50 lines into their first tree and ends them with a
note (checked against all 2,755 of them); it left the free ones whole. publish.py cuts every
preview with this, and the tests check every file in static/assets/previews against it.

The cut keeps the first tree and nothing after it: with small trees, 50 lines held two or three of
them, and with three small ones a whole forest (ADBE 1Day 1S00, sold for 69 US$, until 14 Nov 2026).
"""
PREVIEW_TREE_LINES = 50
PREVIEW_TAIL = "\n\t...\nThe rest of this Pine script is part of the paid version. Visit the website for more info.\n"


def cut_preview(script: str) -> str:
    """The public part of a script: the lines before its first tree and that tree, or only its first
    PREVIEW_TREE_LINES lines if it is longer. A preview that is already cut is cut again by the same
    rule (one cut before 14 Nov 2026 may hold more than one tree); one cut by it comes back unchanged."""
    body = script[:-len(PREVIEW_TAIL)] if script.endswith(PREVIEW_TAIL) else script
    lines = body.replace("\r\n", "\n").split("\n")
    start = next((i for i, line in enumerate(lines) if line.startswith("decision_tree_")), None)
    if start is None:
        raise ValueError("no decision_tree_ function: not a strategy script")
    # the function ends at the first line that is neither blank nor indented: the next tree, the indicator
    end = next((i for i in range(start + 1, len(lines)) if lines[i][:1] not in ("", " ", "\t")), len(lines))
    keep = lines[:min(end, start + PREVIEW_TREE_LINES)]
    while keep and not keep[-1].strip():
        keep.pop()
    return "\n".join(keep) + "\n" + PREVIEW_TAIL
