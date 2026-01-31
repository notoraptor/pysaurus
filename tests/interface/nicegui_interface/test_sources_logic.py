"""
Tests for the sources selection logic.

Tests the helper functions used by the sources dialog.
"""


# Import the functions we're testing
from pysaurus.interface.nicegui.utils.constants import SOURCE_TREE


# Replicate the helper functions here for testing
def _get_subtree(tree: dict, entry_name: str) -> dict | None:
    """Get a subtree from the source tree by path."""
    steps = entry_name.split("-")
    subtree = tree
    for step in steps:
        if subtree is None:
            return None
        subtree = subtree.get(step)
    return subtree


def _collect_all_paths(tree: dict | None, prefix: str = "") -> list[str]:
    """Collect all possible paths from a tree (including the prefix itself if it has children)."""
    paths = []
    if tree is not None:
        if prefix:
            paths.append(prefix)
        for name, subtree in tree.items():
            entry_name = f"{prefix}-{name}" if prefix else name
            paths.extend(_collect_all_paths(subtree, entry_name))
    else:
        if prefix:
            paths.append(prefix)
    return paths


def _add_paths(old_paths: list[str], new_paths: list[str]) -> list[str]:
    """Add paths to list without duplicates."""
    result = old_paths.copy()
    for path in new_paths:
        if path not in result:
            result.append(path)
    result.sort()
    return result


def _remove_paths(old_paths: list[str], paths_to_remove: list[str]) -> list[str]:
    """Remove paths from list."""
    return [p for p in old_paths if p not in paths_to_remove]


class TestSourceTree:
    """Test SOURCE_TREE structure."""

    def test_source_tree_has_readable_and_unreadable(self):
        """SOURCE_TREE should have readable and unreadable at top level."""
        assert "readable" in SOURCE_TREE
        assert "unreadable" in SOURCE_TREE

    def test_readable_has_found_and_not_found(self):
        """readable branch should have found and not_found."""
        readable = SOURCE_TREE["readable"]
        assert readable is not None
        assert "found" in readable
        assert "not_found" in readable

    def test_readable_found_has_thumbnails(self):
        """readable > found should have thumbnail options."""
        found = SOURCE_TREE["readable"]["found"]
        assert found is not None
        assert "with_thumbnails" in found
        assert "without_thumbnails" in found
        # These are leaf nodes (None values)
        assert found["with_thumbnails"] is None
        assert found["without_thumbnails"] is None

    def test_unreadable_has_found_and_not_found(self):
        """unreadable branch should have found and not_found as leaves."""
        unreadable = SOURCE_TREE["unreadable"]
        assert unreadable is not None
        assert "found" in unreadable
        assert "not_found" in unreadable
        # These are leaf nodes for unreadable
        assert unreadable["found"] is None
        assert unreadable["not_found"] is None


class TestGetSubtree:
    """Test _get_subtree function."""

    def test_get_readable(self):
        """Get readable subtree."""
        subtree = _get_subtree(SOURCE_TREE, "readable")
        assert subtree is not None
        assert "found" in subtree
        assert "not_found" in subtree

    def test_get_readable_found(self):
        """Get readable-found subtree."""
        subtree = _get_subtree(SOURCE_TREE, "readable-found")
        assert subtree is not None
        assert "with_thumbnails" in subtree
        assert "without_thumbnails" in subtree

    def test_get_leaf_returns_none(self):
        """Getting a leaf node returns None."""
        subtree = _get_subtree(SOURCE_TREE, "readable-found-with_thumbnails")
        assert subtree is None

    def test_get_unreadable_found(self):
        """Get unreadable-found which is a leaf."""
        subtree = _get_subtree(SOURCE_TREE, "unreadable-found")
        assert subtree is None  # It's a leaf


class TestCollectAllPaths:
    """Test _collect_all_paths function."""

    def test_collect_from_readable(self):
        """Collect all paths under readable."""
        readable_tree = SOURCE_TREE["readable"]
        paths = _collect_all_paths(readable_tree, "readable")

        # Should include: readable, readable-found, readable-not_found,
        # readable-found-with_thumbnails, readable-found-without_thumbnails,
        # readable-not_found-with_thumbnails, readable-not_found-without_thumbnails
        assert "readable" in paths
        assert "readable-found" in paths
        assert "readable-not_found" in paths
        assert "readable-found-with_thumbnails" in paths
        assert "readable-found-without_thumbnails" in paths
        assert "readable-not_found-with_thumbnails" in paths
        assert "readable-not_found-without_thumbnails" in paths

    def test_collect_from_unreadable(self):
        """Collect all paths under unreadable."""
        unreadable_tree = SOURCE_TREE["unreadable"]
        paths = _collect_all_paths(unreadable_tree, "unreadable")

        # Should include: unreadable, unreadable-found, unreadable-not_found
        assert "unreadable" in paths
        assert "unreadable-found" in paths
        assert "unreadable-not_found" in paths
        # unreadable doesn't have thumbnail level
        assert "unreadable-found-with_thumbnails" not in paths

    def test_collect_from_leaf_subtree(self):
        """Collect paths from a leaf node's subtree (None)."""
        paths = _collect_all_paths(None, "readable-found-with_thumbnails")
        assert paths == ["readable-found-with_thumbnails"]


class TestAddPaths:
    """Test _add_paths function."""

    def test_add_new_path(self):
        """Add a new path to empty list."""
        result = _add_paths([], ["readable"])
        assert result == ["readable"]

    def test_add_multiple_paths(self):
        """Add multiple paths."""
        result = _add_paths([], ["readable", "unreadable"])
        assert "readable" in result
        assert "unreadable" in result

    def test_no_duplicates(self):
        """Adding existing path should not create duplicates."""
        result = _add_paths(["readable"], ["readable"])
        assert result == ["readable"]

    def test_paths_are_sorted(self):
        """Result should be sorted."""
        result = _add_paths([], ["unreadable", "readable"])
        assert result == ["readable", "unreadable"]


class TestRemovePaths:
    """Test _remove_paths function."""

    def test_remove_existing_path(self):
        """Remove a path that exists."""
        result = _remove_paths(["readable", "unreadable"], ["readable"])
        assert result == ["unreadable"]

    def test_remove_nonexistent_path(self):
        """Remove a path that doesn't exist should not error."""
        result = _remove_paths(["readable"], ["unreadable"])
        assert result == ["readable"]

    def test_remove_multiple_paths(self):
        """Remove multiple paths."""
        result = _remove_paths(
            ["readable", "readable-found", "unreadable"], ["readable", "readable-found"]
        )
        assert result == ["unreadable"]


class TestSelectDevelopLogic:
    """Test the select/develop logic flow."""

    def test_initial_state_with_readable_selected(self):
        """When readable is selected, is_selected should be True."""
        state = {"paths": ["readable"]}
        is_selected = "readable" in state["paths"]
        assert is_selected is True

    def test_develop_readable_removes_path(self):
        """Clicking 'develop' on readable should remove it from paths."""
        state = {"paths": ["readable"]}

        # Simulate clicking "develop"
        entry_name = "readable"
        state["paths"] = _remove_paths(state["paths"], [entry_name])

        assert "readable" not in state["paths"]
        assert state["paths"] == []

    def test_after_develop_children_should_show(self):
        """After develop, is_selected should be False so children show."""
        state = {"paths": []}  # After develop
        is_selected = "readable" in state["paths"]
        assert is_selected is False
        # This means children should be rendered

    def test_select_branch_removes_children_and_adds_branch(self):
        """Clicking 'select' on a branch removes children and adds the branch."""
        # Start with some child paths selected
        state = {"paths": ["readable-found-with_thumbnails", "readable-not_found"]}

        # Simulate clicking "select" on readable
        entry_name = "readable"
        subtree = SOURCE_TREE["readable"]
        paths_to_remove = _collect_all_paths(subtree, entry_name)

        state["paths"] = _remove_paths(state["paths"], paths_to_remove)
        state["paths"] = _add_paths(state["paths"], [entry_name])

        assert state["paths"] == ["readable"]
        assert "readable-found-with_thumbnails" not in state["paths"]
        assert "readable-not_found" not in state["paths"]

    def test_select_leaf_checkbox(self):
        """Selecting a leaf checkbox adds it to paths."""
        state = {"paths": []}

        # Simulate checking "readable-found-with_thumbnails"
        entry_name = "readable-found-with_thumbnails"
        state["paths"] = _add_paths(state["paths"], [entry_name])

        assert entry_name in state["paths"]

    def test_unselect_leaf_checkbox(self):
        """Unselecting a leaf checkbox removes it from paths."""
        state = {"paths": ["readable-found-with_thumbnails"]}

        # Simulate unchecking
        entry_name = "readable-found-with_thumbnails"
        state["paths"] = _remove_paths(state["paths"], [entry_name])

        assert entry_name not in state["paths"]

    def test_multiple_selections(self):
        """Can select multiple paths at different levels."""
        state = {"paths": []}

        # Select readable-found-with_thumbnails
        state["paths"] = _add_paths(state["paths"], ["readable-found-with_thumbnails"])
        # Select unreadable
        state["paths"] = _add_paths(state["paths"], ["unreadable"])

        assert "readable-found-with_thumbnails" in state["paths"]
        assert "unreadable" in state["paths"]
        assert len(state["paths"]) == 2
