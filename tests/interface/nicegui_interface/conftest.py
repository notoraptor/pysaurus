"""
Pytest configuration for NiceGUI interface tests.

Activates the nicegui.testing plugin for User/Screen fixtures.
"""

import pytest
from unittest.mock import MagicMock, patch

# Activate nicegui testing plugin
pytest_plugins = ["nicegui.testing.plugin"]


class MockApplication:
    """Mock application for testing."""

    def get_database_names(self):
        return ["test_database", "another_database"]


class MockAPIBridge:
    """
    Mock API bridge for UI testing.

    Provides the same interface as APIBridge but with mock data.
    """

    def __init__(self, mock_database):
        self._database = mock_database
        self._application = MockApplication()

    @property
    def api(self):
        """Return a mock API object."""
        class MockAPI:
            def __init__(self, db, app):
                self.database = db
                self.application = app

        return MockAPI(self._database, self._application)

    def get_database_names(self):
        return ["test_database", "another_database"]

    def get_constants(self):
        return {
            "PYTHON_APP_NAME": "Pysaurus",
            "PYTHON_DEFAULT_SOURCES": [],
        }

    def describe_prop_types(self):
        return self._database.get_prop_types() if self._database else []

    def backend(self, page_size, page_number, selector=None):
        if self._database:
            ctx = self._database.provider.get_current_state(page_size, page_number, selector)
            from pysaurus.video.database_context import DatabaseContext

            db_ctx = DatabaseContext(
                name=self._database.get_name(),
                folders=self._database.get_folders(),
                prop_types=self._database.get_prop_types(),
                view=ctx,
            )
            return db_ctx.json()
        return {"videos": [], "pageSize": page_size, "pageNumber": page_number, "nbPages": 0, "nbVideos": 0}

    def set_search(self, text, cond="and"):
        if self._database:
            self._database.provider.set_search(text, cond)
        return {"error": False}

    def set_sources(self, paths):
        if self._database:
            self._database.provider.set_sources(paths)
        return {"error": False}

    def set_groups(self, field, is_property=False, sorting="field", reverse=False, allow_singletons=True):
        if self._database:
            self._database.provider.set_groups(field, is_property, sorting, reverse, allow_singletons)
        return {"error": False}

    def set_sorting(self, sorting):
        if self._database:
            self._database.provider.set_sort(sorting)
        return {"error": False}

    def create_prop_type(self, name, prop_type, definition, multiple):
        if self._database:
            try:
                self._database.prop_type_add(name, prop_type, definition, multiple)
                return {"error": False}
            except Exception as e:
                return {"error": True, "data": {"name": type(e).__name__, "message": str(e)}}
        return {"error": True, "data": {"message": "No database"}}

    def remove_prop_type(self, name):
        if self._database:
            try:
                self._database.prop_type_del(name)
                return {"error": False}
            except Exception as e:
                return {"error": True, "data": {"name": type(e).__name__, "message": str(e)}}
        return {"error": True, "data": {"message": "No database"}}

    def rename_prop_type(self, old_name, new_name):
        if self._database:
            try:
                self._database.prop_type_set_name(old_name, new_name)
                return {"error": False}
            except Exception as e:
                return {"error": True, "data": {"name": type(e).__name__, "message": str(e)}}
        return {"error": True, "data": {"message": "No database"}}

    def convert_prop_multiplicity(self, name, multiple):
        if self._database:
            try:
                self._database.prop_type_set_multiple(name, multiple)
                return {"error": False}
            except Exception as e:
                return {"error": True, "data": {"name": type(e).__name__, "message": str(e)}}
        return {"error": True, "data": {"message": "No database"}}

    def open_database(self, name, update=True):
        return {"error": False}

    def create_database(self, name, folders, update=True):
        return {"error": False}

    def close_database(self):
        return {"error": False}

    def delete_database(self):
        return {"error": False}

    def rename_database(self, new_name):
        return {"error": False}

    def select_directory(self):
        return None  # Don't show dialog in tests

    def select_file(self):
        return None

    def close_app(self):
        pass

    def add_notification_handler(self, handler):
        pass

    def remove_notification_handler(self, handler):
        pass


@pytest.fixture
def mock_api_bridge(mock_database, monkeypatch):
    """
    Create a mock API bridge for UI testing.

    Patches the global api_bridge in nicegui modules to use mock database.
    """
    bridge = MockAPIBridge(mock_database)

    # Patch the global api_bridge in all modules that use it
    import pysaurus.interface.nicegui.pages.databases_page as databases_page
    import pysaurus.interface.nicegui.pages.videos_page as videos_page
    import pysaurus.interface.nicegui.pages.properties_page as properties_page
    import pysaurus.interface.nicegui.pages.home_page as home_page
    import pysaurus.interface.nicegui.main as main_module

    monkeypatch.setattr(databases_page, "api_bridge", bridge)
    monkeypatch.setattr(videos_page, "api_bridge", bridge)
    monkeypatch.setattr(properties_page, "api_bridge", bridge)
    monkeypatch.setattr(home_page, "api_bridge", bridge)
    monkeypatch.setattr(main_module, "api_bridge", bridge)

    return bridge


@pytest.fixture
def reset_app_state(monkeypatch):
    """Reset app_state to initial values before each test."""
    from pysaurus.interface.nicegui.state import AppState, Page

    fresh_state = AppState()

    import pysaurus.interface.nicegui.state as state_module
    import pysaurus.interface.nicegui.pages.databases_page as databases_page
    import pysaurus.interface.nicegui.pages.videos_page as videos_page
    import pysaurus.interface.nicegui.pages.home_page as home_page
    import pysaurus.interface.nicegui.main as main_module

    monkeypatch.setattr(state_module, "app_state", fresh_state)
    monkeypatch.setattr(databases_page, "app_state", fresh_state)
    monkeypatch.setattr(videos_page, "app_state", fresh_state)
    monkeypatch.setattr(home_page, "app_state", fresh_state)
    monkeypatch.setattr(main_module, "app_state", fresh_state)

    return fresh_state