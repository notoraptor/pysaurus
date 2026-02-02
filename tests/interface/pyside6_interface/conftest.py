"""
Pytest configuration for PySide6 interface tests.

Provides fixtures for testing Qt widgets with mock database.
Uses pytest-qt for Qt event loop management.

Note: mock_database fixture is inherited from tests/conftest.py
Note: pytest-qt plugin is auto-loaded, no need to declare it
"""

import os

# Use offscreen platform to avoid displaying windows during tests
# Must be set before any Qt imports
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from tests.mocks.mock_database import MockDatabase


class MockApplication:
    """Mock Application for testing."""

    def __init__(self):
        self._database_names = ["test_database", "another_database"]

    def get_database_names(self) -> list[str]:
        """Get list of database names."""
        return self._database_names

    def delete_database_from_name(self, name: str) -> None:
        """Delete a database by name."""
        if name in self._database_names:
            self._database_names.remove(name)


class MockAppContext:
    """
    Mock application context for PySide6 testing.

    Provides the same interface as AppContext but with mock database.
    Does not use real Qt signals - only synchronous operations.
    """

    def __init__(self, mock_database: MockDatabase):
        self._database = mock_database
        self._application = MockApplication()

    @property
    def database(self):
        """AbstractDatabase (mock)."""
        return self._database

    @property
    def provider(self):
        """VideoProvider (mock)."""
        return self._database.provider if self._database else None

    @property
    def ops(self):
        """DatabaseOperations (mock)."""
        return self._database.ops if self._database else None

    @property
    def algos(self):
        """DatabaseAlgorithms (mock)."""
        return self._database.algos if self._database else None

    @property
    def application(self):
        """Application (mock)."""
        return self._application

    def get_database_names(self) -> list[str]:
        """Get list of database names."""
        return self._application.get_database_names()

    def get_videos(self, page_size: int, page_number: int, selector=None):
        """Return the context with videos."""
        return self.provider.get_current_state(page_size, page_number, selector)

    def get_database_folders(self) -> list[str]:
        """Get database folders."""
        return [str(f) for f in self._database.get_folders()]

    def classifier_select_group(self, group_id: int) -> None:
        """Add a group value to the classifier path."""
        if self.provider:
            self.provider.classifier_select_group(group_id)

    def classifier_back(self) -> None:
        """Remove the last value from the classifier path."""
        if self.provider:
            self.provider.classifier_back()

    def classifier_reverse(self) -> list:
        """Reverse the classifier path order."""
        if self.provider:
            return self.provider.classifier_reverse()
        return []

    def classifier_focus_prop_val(self, prop_name: str, field_value) -> None:
        """Focus on a specific property value."""
        if self.provider:
            self.provider.classifier_focus_prop_val(prop_name, field_value)

    def apply_on_view(self, selector_dict: dict, operation: str, *args):
        """Apply an operation on selected videos."""
        if self.provider:
            return self.provider.apply_on_view(selector_dict, operation, *args)
        return None

    def confirm_unique_moves(self) -> int:
        """Confirm all unique video moves."""
        return 0

    def rename_database(self, new_name: str) -> None:
        """Rename the database."""
        if self._database:
            self._database.rename(new_name)

    def close_database(self) -> None:
        """Close the database (no-op for mock)."""
        pass

    def set_database_folders(self, folders: list[str]) -> None:
        """Set database folders (no-op for mock)."""
        pass


@pytest.fixture
def mock_context(mock_database):
    """
    Create a mock application context.

    Args:
        mock_database: MockDatabase fixture from tests/conftest.py

    Returns:
        MockAppContext: Mock context wrapping the mock database
    """
    return MockAppContext(mock_database)


@pytest.fixture
def prop_types(mock_database):
    """
    Get property types from mock database.

    Returns:
        list[dict]: List of property type definitions
    """
    return mock_database.get_prop_types()


@pytest.fixture
def test_videos(mock_database):
    """
    Get test videos from mock database.

    Returns:
        list[MockVideoPattern]: List of test videos
    """
    return mock_database.get_videos()


@pytest.fixture
def video_search_context(mock_context):
    """
    Get a video search context with default settings.

    Returns:
        VideoSearchContext: Context with first page of videos
    """
    return mock_context.get_videos(page_size=20, page_number=0)
