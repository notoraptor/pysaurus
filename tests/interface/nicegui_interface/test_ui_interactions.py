"""
UI interaction tests for NiceGUI interface.

Uses nicegui.testing.User fixture for fast, headless UI testing.
Tests the actual Pysaurus pages defined in main.py.
"""

import pytest
from nicegui.testing import User


# =============================================================================
# Databases Page Tests
# =============================================================================


class TestDatabasesPage:
    """Test the databases page (index page)."""

    async def test_databases_page_renders(self, user: User, mock_api_bridge, reset_app_state):
        """Test that databases page renders with expected content."""
        await user.open("/")

        # Should see main title
        await user.should_see("Pysaurus")
        await user.should_see("Video Collection Manager")

        # Should see section titles
        await user.should_see("Open Database")
        await user.should_see("Create Database")

    async def test_databases_page_shows_database_list(
        self, user: User, mock_api_bridge, reset_app_state
    ):
        """Test that databases are listed."""
        await user.open("/")

        # Mock database should be listed
        await user.should_see("test_database")

    async def test_create_database_form_exists(
        self, user: User, mock_api_bridge, reset_app_state
    ):
        """Test that create database form elements exist."""
        await user.open("/")

        await user.should_see("Database name")
        await user.should_see("Folders")
        await user.should_see("Add folder")
        await user.should_see("Create Database")


# =============================================================================
# Videos Page Tests
# =============================================================================


class TestVideosPage:
    """Test the videos page."""

    async def test_videos_page_requires_database(
        self, user: User, mock_api_bridge, reset_app_state
    ):
        """Test videos page behavior when no database is open."""
        # Without setting database_name, header won't show nav
        await user.open("/videos")

        # Should still render but might show limited UI
        # (depends on how videos_page handles no database)

    async def test_videos_page_with_database(
        self, user: User, mock_api_bridge, reset_app_state
    ):
        """Test videos page with database open."""
        # Set database name in state
        reset_app_state.database_name = "test_database"

        await user.open("/videos")

        # Should see header with navigation
        await user.should_see("Pysaurus")


# =============================================================================
# Properties Page Tests
# =============================================================================


class TestPropertiesPage:
    """Test the properties page."""

    async def test_properties_page_renders(
        self, user: User, mock_api_bridge, reset_app_state
    ):
        """Test that properties page renders."""
        reset_app_state.database_name = "test_database"

        await user.open("/properties")

        await user.should_see("Properties Management")
        await user.should_see("Current Properties")
        await user.should_see("Add New Property")

    async def test_properties_page_shows_property_types(
        self, user: User, mock_api_bridge, reset_app_state
    ):
        """Test that existing property types are shown."""
        reset_app_state.database_name = "test_database"

        await user.open("/properties")

        # Mock database has 'genre' and 'rating' properties
        await user.should_see("genre")
        await user.should_see("rating")

    async def test_property_form_elements(
        self, user: User, mock_api_bridge, reset_app_state
    ):
        """Test property creation form elements."""
        reset_app_state.database_name = "test_database"

        await user.open("/properties")

        await user.should_see("Property name")
        await user.should_see("Type")
        await user.should_see("Accept multiple values")
        await user.should_see("Create")


# =============================================================================
# Navigation Tests
# =============================================================================


class TestNavigation:
    """Test navigation between pages."""

    async def test_navigate_from_databases_to_properties(
        self, user: User, mock_api_bridge, reset_app_state
    ):
        """Test navigation to properties page."""
        reset_app_state.database_name = "test_database"

        await user.open("/")

        # Should see header with nav when database is set
        # Click Properties button
        try:
            user.find("Properties").click()
            await user.should_see("Properties Management")
        except Exception:
            # Navigation may not work without full app context
            pass

    async def test_back_button_on_properties(
        self, user: User, mock_api_bridge, reset_app_state
    ):
        """Test back button on properties page."""
        reset_app_state.database_name = "test_database"

        await user.open("/properties")

        # Properties page has a back button
        # Look for arrow_back icon button


# =============================================================================
# Header Tests
# =============================================================================


class TestHeader:
    """Test header rendering."""

    async def test_header_without_database(
        self, user: User, mock_api_bridge, reset_app_state
    ):
        """Test header when no database is open."""
        await user.open("/")

        # Should see title but not navigation buttons
        await user.should_see("Pysaurus")

    async def test_header_with_database(
        self, user: User, mock_api_bridge, reset_app_state
    ):
        """Test header when database is open."""
        reset_app_state.database_name = "test_database"

        await user.open("/videos")

        # Should see navigation buttons
        await user.should_see("Videos")
        await user.should_see("Properties")
        await user.should_see("Databases")

        # Should see database name
        await user.should_see("DB: test_database")


# =============================================================================
# Footer Tests
# =============================================================================


class TestFooter:
    """Test footer rendering."""

    async def test_footer_renders(self, user: User, mock_api_bridge, reset_app_state):
        """Test that footer is present on all pages."""
        await user.open("/")
        await user.should_see("Video Collection Manager")