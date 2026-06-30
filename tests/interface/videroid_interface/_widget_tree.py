"""Static widget-tree helpers for videroid widget tests.

Thin wrappers over videre's own ``Widget.collect_matches`` — the recursive
traversal (via ``_controls()``) that ``StepWindow.find`` is itself built on — so
a test can assert what a widget actually built (texts present, a
Picture/Checkbox/badge exists) WITHOUT rendering. ``collect_matches`` works on a
detached widget (a dialog or card built standalone, not mounted in a window),
which ``StepWindow.find`` cannot reach.
"""

from __future__ import annotations

import videre


def find(widget, cls):
    """Every widget of type ``cls`` in the subtree (root included), in order."""
    return widget.collect_matches(lambda w: isinstance(w, cls))


def texts(widget):
    """The ``.text`` of every ``videre.Text`` in the subtree, in reading order."""
    return [w.text for w in find(widget, videre.Text)]
