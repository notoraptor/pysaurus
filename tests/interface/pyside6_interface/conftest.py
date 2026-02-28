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

    # State

    def has_database(self) -> bool:
        return self._database is not None

    def get_database_name(self) -> str:
        return self._database.get_name() if self._database else ""

    def get_database_folder_path(self) -> str:
        return str(self._database.ways.db_folder) if self._database else ""

    # Application

    def get_database_names(self) -> list[str]:
        return self._application.get_database_names()

    def delete_database_by_name(self, name: str) -> None:
        self._application.delete_database_from_name(name)

    # Property types

    def get_prop_types(self, **kwargs) -> list[dict]:
        if self._database:
            return self._database.get_prop_types(**kwargs)
        return []

    def create_prop_type(self, name, prop_type, definition, multiple) -> None:
        self._database.prop_type_add(name, prop_type, definition, multiple)

    def rename_prop_type(self, name, new_name) -> None:
        self._database.prop_type_set_name(name, new_name)

    def delete_prop_type(self, name) -> None:
        self._database.prop_type_del(name)

    def set_prop_type_multiple(self, name, multiple) -> None:
        self._database.prop_type_set_multiple(name, multiple)

    # Video entries

    def delete_video_entry(self, video_id) -> None:
        if self._database:
            self._database.video_entry_del(video_id)

    def get_video_by_id(self, video_id):
        if not self._database:
            return None
        videos = self._database.get_videos(where={"video_id": video_id})
        return videos[0] if videos else None

    # Video operations

    def open_video(self, video_id) -> None:
        if self._database and self._database.ops:
            self._database.ops.open_video(video_id)

    def rename_video(self, video_id, new_title) -> None:
        if self._database and self._database.ops:
            self._database.ops.change_video_file_title(video_id, new_title)

    def dismiss_similarity(self, video_id) -> None:
        if self._database and self._database.ops:
            self._database.ops.set_similarities_from_list([video_id], [-1])

    def reset_similarity(self, video_id) -> None:
        if self._database and self._database.ops:
            self._database.ops.set_similarities_from_list([video_id], [None])

    def mark_as_read(self, video_id) -> None:
        if self._database and self._database.ops:
            self._database.ops.mark_as_read(video_id)

    def trash_video(self, video_id) -> None:
        if self._database and self._database.ops:
            self._database.ops.trash_video(video_id)

    def delete_video_file(self, video_id) -> None:
        if self._database and self._database.ops:
            self._database.ops.delete_video(video_id)

    # Provider / view

    def get_videos(self, page_size: int, page_number: int, selector=None):
        provider = self._database.provider if self._database else None
        return provider.get_current_state(page_size, page_number, selector)

    def set_group(self, group_id) -> None:
        provider = self._database.provider if self._database else None
        if provider:
            provider.set_group(group_id)

    def notify_attributes_modified(self, fields, is_property) -> None:
        provider = self._database.provider if self._database else None
        if provider:
            provider.manage_attributes_modified(fields, is_property=is_property)

    def get_provider_state(self):
        provider = self._database.provider if self._database else None
        if provider:
            return provider.get_current_state(1, 0)
        return None

    def set_sources(self, sources) -> None:
        provider = self._database.provider if self._database else None
        if provider:
            provider.set_sources(sources)

    def set_groups(self, *, field, is_property, sorting, reverse, allow_singletons) -> None:
        provider = self._database.provider if self._database else None
        if provider:
            provider.set_groups(
                field=field,
                is_property=is_property,
                sorting=sorting,
                reverse=reverse,
                allow_singletons=allow_singletons,
            )

    def clear_groups(self) -> None:
        provider = self._database.provider if self._database else None
        if provider:
            provider.set_groups(None)

    def set_search(self, text, cond) -> None:
        provider = self._database.provider if self._database else None
        if provider:
            provider.set_search(text, cond)

    def set_sorting(self, sorting) -> None:
        provider = self._database.provider if self._database else None
        if provider:
            provider.set_sort(sorting)

    def get_random_video_id(self):
        provider = self._database.provider if self._database else None
        if provider:
            return provider.get_random_found_video_id()
        return None

    def reset_grouping_and_classifier(self) -> None:
        provider = self._database.provider if self._database else None
        if provider:
            provider.reset_parameters(
                provider.LAYER_GROUPING,
                provider.LAYER_CLASSIFIER,
                provider.LAYER_GROUP,
            )

    # API

    def playlist(self) -> str:
        return ""

    def open_from_server(self, video_id) -> None:
        pass

    def open_containing_folder(self, video_id) -> None:
        pass

    # Property values (for dialogs)

    def get_property_values(self, prop_name) -> dict[int, list]:
        if self._database:
            return self._database.videos_tag_get(prop_name)
        return {}

    def delete_property_values(self, prop_name, values) -> None:
        if self._database and self._database.algos:
            self._database.algos.delete_property_values(prop_name, values)

    def replace_property_values(self, prop_name, old_values, new_value) -> bool:
        if self._database and self._database.algos:
            return self._database.algos.replace_property_values(
                prop_name, old_values, new_value
            )
        return False

    def apply_on_prop_value(self, prop_name, modifier) -> None:
        if self._database and self._database.ops:
            self._database.ops.apply_on_prop_value(prop_name, modifier)

    def set_video_properties(self, video_id, properties) -> None:
        if self._database:
            self._database.video_entry_set_tags(video_id, properties)

    # Algorithms

    def move_property_values(self, values, from_name, to_name, *, concatenate) -> int:
        if self._database and self._database.algos:
            return self._database.algos.move_property_values(
                values, from_name, to_name, concatenate=concatenate
            )
        return 0

    def fill_property_with_terms(self, prop_name, *, only_empty) -> None:
        if self._database and self._database.algos:
            self._database.algos.fill_property_with_terms(
                prop_name, only_empty=only_empty
            )

    # Other existing methods

    def get_database_folders(self) -> list[str]:
        if self._database:
            return [str(f) for f in self._database.get_folders()]
        return []

    def classifier_select_group(self, group_id: int) -> None:
        provider = self._database.provider if self._database else None
        if provider:
            provider.classifier_select_group(group_id)

    def classifier_back(self) -> None:
        provider = self._database.provider if self._database else None
        if provider:
            provider.classifier_back()

    def classifier_reverse(self) -> list:
        provider = self._database.provider if self._database else None
        if provider:
            return provider.classifier_reverse()
        return []

    def classifier_focus_prop_val(self, prop_name: str, field_value) -> None:
        provider = self._database.provider if self._database else None
        if provider:
            provider.classifier_focus_prop_val(prop_name, field_value)

    def apply_on_view(self, selector_dict: dict, operation: str, *args):
        provider = self._database.provider if self._database else None
        if provider:
            return provider.apply_on_view(selector_dict, operation, *args)
        return None

    def confirm_unique_moves(self) -> int:
        return 0

    def confirm_move(self, src_video_id: int, dst_video_id: int) -> None:
        pass

    def rename_database(self, new_name: str) -> None:
        if self._database:
            self._database.rename(new_name)

    def close_database(self) -> None:
        pass

    def close_app(self) -> None:
        pass

    def set_database_folders(self, folders: list[str]) -> None:
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
