"""
Tests for video operations in PySide6 interface.

Tests:
- Video deletion
- Property modifications (batch edit)
"""

from PySide6.QtWidgets import QApplication, QMessageBox


def make_video_dicts(count: int) -> list[dict]:
    """Create a list of mock video dictionaries."""
    videos = []
    for i in range(count):
        videos.append(
            {
                "video_id": i + 1,
                "filename": f"/videos/test_video_{i + 1}.mp4",
                "file_size": 1024 * 1024 * (i + 1),
                "mtime": 1700000000.0 + i,
                "duration": 3600,
                "duration_time_base": 1,
                "height": 1080,
                "width": 1920,
                "meta_title": f"Video {i + 1}",
                "found": True,
                "unreadable": False,
                "watched": False,
                "with_thumbnails": True,
                "video_codec": "h264",
                "video_codec_description": "H.264",
                "audio_codec": "aac",
                "channels": 2,
                "sample_rate": 44100,
                "audio_bit_rate": 128000,
                "container_format": "mp4",
                "frame_rate_num": 30,
                "frame_rate_den": 1,
                "date_entry_modified": "2024-01-15",
                "similarity_id": None,
                "properties": {"genre": ["action"], "rating": [5]},
            }
        )
    return videos


class TestVideoPropertyModification:
    """Tests for modifying video properties."""

    def test_count_property_values(self, qtbot, mock_context):
        """Test counting property values for selected videos."""
        # Set up videos with different property values
        videos = make_video_dicts(5)
        videos[0]["properties"] = {"genre": ["action", "comedy"]}
        videos[1]["properties"] = {"genre": ["action"]}
        videos[2]["properties"] = {"genre": ["drama"]}
        videos[3]["properties"] = {"genre": ["action", "drama"]}
        videos[4]["properties"] = {"genre": []}
        mock_context._database._videos = videos

        # Count genre values for all videos
        selector = {"mode": "exclude", "selection": []}  # Select all
        result = mock_context.provider.apply_on_view(
            selector, "count_property_values", "genre"
        )

        # Convert to dict for easier checking
        counts = {val: count for val, count in result}

        assert counts.get("action") == 3
        assert counts.get("drama") == 2
        assert counts.get("comedy") == 1

    def test_count_property_values_with_selection(self, qtbot, mock_context):
        """Test counting property values for specific video selection."""
        videos = make_video_dicts(5)
        videos[0]["properties"] = {"genre": ["action"]}
        videos[1]["properties"] = {"genre": ["action"]}
        videos[2]["properties"] = {"genre": ["drama"]}
        mock_context._database._videos = videos

        # Count only videos 1 and 2
        selector = {"mode": "include", "selection": [1, 2]}
        result = mock_context.provider.apply_on_view(
            selector, "count_property_values", "genre"
        )

        counts = {val: count for val, count in result}

        assert counts.get("action") == 2
        assert counts.get("drama") is None  # video 3 not selected

    def test_edit_property_add_values(self, qtbot, mock_context):
        """Test adding property values to videos."""
        videos = make_video_dicts(3)
        videos[0]["properties"] = {"genre": ["action"]}
        videos[1]["properties"] = {"genre": ["drama"]}
        videos[2]["properties"] = {"genre": []}
        mock_context._database._videos = videos

        # Add "comedy" to all videos
        selector = {"mode": "exclude", "selection": []}
        mock_context.provider.apply_on_view(
            selector, "edit_property_for_videos", "genre", ["comedy"], []
        )

        # Check all videos now have "comedy"
        for video in mock_context._database._videos:
            assert "comedy" in video["properties"]["genre"]

        # Original values should still be there
        assert "action" in mock_context._database._videos[0]["properties"]["genre"]
        assert "drama" in mock_context._database._videos[1]["properties"]["genre"]

    def test_edit_property_remove_values(self, qtbot, mock_context):
        """Test removing property values from videos."""
        videos = make_video_dicts(3)
        videos[0]["properties"] = {"genre": ["action", "comedy"]}
        videos[1]["properties"] = {"genre": ["action", "drama"]}
        videos[2]["properties"] = {"genre": ["comedy"]}
        mock_context._database._videos = videos

        # Remove "action" from all videos
        selector = {"mode": "exclude", "selection": []}
        mock_context.provider.apply_on_view(
            selector, "edit_property_for_videos", "genre", [], ["action"]
        )

        # Check "action" is removed
        assert "action" not in mock_context._database._videos[0]["properties"]["genre"]
        assert "action" not in mock_context._database._videos[1]["properties"]["genre"]

        # Other values should remain
        assert "comedy" in mock_context._database._videos[0]["properties"]["genre"]
        assert "drama" in mock_context._database._videos[1]["properties"]["genre"]
        assert "comedy" in mock_context._database._videos[2]["properties"]["genre"]

    def test_edit_property_add_and_remove(self, qtbot, mock_context):
        """Test adding and removing values in the same operation."""
        videos = make_video_dicts(2)
        videos[0]["properties"] = {"genre": ["action", "comedy"]}
        videos[1]["properties"] = {"genre": ["action"]}
        mock_context._database._videos = videos

        # Replace "action" with "thriller"
        selector = {"mode": "exclude", "selection": []}
        mock_context.provider.apply_on_view(
            selector, "edit_property_for_videos", "genre", ["thriller"], ["action"]
        )

        # Check both videos
        assert "thriller" in mock_context._database._videos[0]["properties"]["genre"]
        assert "action" not in mock_context._database._videos[0]["properties"]["genre"]
        assert "comedy" in mock_context._database._videos[0]["properties"]["genre"]

        assert "thriller" in mock_context._database._videos[1]["properties"]["genre"]
        assert "action" not in mock_context._database._videos[1]["properties"]["genre"]

    def test_edit_property_with_partial_selection(self, qtbot, mock_context):
        """Test editing properties for only selected videos."""
        videos = make_video_dicts(3)
        videos[0]["properties"] = {"genre": ["action"]}
        videos[1]["properties"] = {"genre": ["action"]}
        videos[2]["properties"] = {"genre": ["action"]}
        mock_context._database._videos = videos

        # Only modify videos 1 and 2
        selector = {"mode": "include", "selection": [1, 2]}
        mock_context.provider.apply_on_view(
            selector, "edit_property_for_videos", "genre", ["comedy"], []
        )

        # Videos 1 and 2 should have comedy
        assert "comedy" in mock_context._database._videos[0]["properties"]["genre"]
        assert "comedy" in mock_context._database._videos[1]["properties"]["genre"]

        # Video 3 should NOT have comedy (not selected)
        assert "comedy" not in mock_context._database._videos[2]["properties"]["genre"]

    def test_batch_edit_dialog_applies_changes(self, qtbot, mock_context, monkeypatch):
        """Test that batch edit through VideosPage applies changes to database."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        # Set up videos
        videos = make_video_dicts(3)
        videos[0]["properties"] = {"genre": ["action"]}
        videos[1]["properties"] = {"genre": ["drama"]}
        videos[2]["properties"] = {"genre": ["comedy"]}
        mock_context._database._videos = videos

        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.show()
        qtbot.waitExposed(page)

        page.refresh()
        QApplication.processEvents()

        # Select all videos using select_all (exclude mode with empty selection = all)
        page._selector.select_all()

        # Mock the dialog to return changes
        from pysaurus.interface.pyside6.dialogs.batch_edit_property_dialog import (
            BatchEditPropertyDialog,
        )

        monkeypatch.setattr(
            BatchEditPropertyDialog,
            "edit_property",
            staticmethod(
                lambda prop_name,
                prop_type,
                nb_videos,
                values_and_counts,
                parent=None: (["horror"], ["action"])
            ),
        )

        # Get a prop_type
        prop_types = mock_context._database.get_prop_types()
        genre_prop = next(pt for pt in prop_types if pt["name"] == "genre")

        # Call the edit method directly
        page._edit_property_for_selection(genre_prop)

        # Verify changes were applied
        # Video 0 should have horror instead of action
        assert "horror" in mock_context._database._videos[0]["properties"]["genre"]
        assert "action" not in mock_context._database._videos[0]["properties"]["genre"]


class TestVideoDeletion:
    """Tests for video deletion."""

    def test_delete_single_video(self, qtbot, mock_context):
        """Test deleting a single video from database."""
        videos = make_video_dicts(5)
        mock_context._database._videos = videos

        initial_count = len(mock_context._database._videos)

        # Delete video with ID 3
        result = mock_context._database.video_entry_del(3)

        assert result is True
        assert len(mock_context._database._videos) == initial_count - 1

        # Verify video 3 is gone
        video_ids = [v["video_id"] for v in mock_context._database._videos]
        assert 3 not in video_ids

    def test_delete_nonexistent_video(self, qtbot, mock_context):
        """Test deleting a video that doesn't exist."""
        videos = make_video_dicts(3)
        mock_context._database._videos = videos

        # Try to delete non-existent video
        result = mock_context._database.video_entry_del(999)

        assert result is False
        assert len(mock_context._database._videos) == 3

    def test_delete_selected_videos_via_page(self, qtbot, mock_context, monkeypatch):
        """Test deleting selected videos through VideosPage."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        videos = make_video_dicts(5)
        mock_context._database._videos = videos

        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.show()
        qtbot.waitExposed(page)

        page.refresh()
        QApplication.processEvents()

        # Select videos 2 and 4
        page._selector.deselect_all()
        page._selector.include(2)
        page._selector.include(4)
        page._selected_video_ids = {2, 4}

        # Mock QMessageBox to accept deletion
        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
        )

        # Call delete
        page._delete_selected()

        # Verify videos are deleted
        video_ids = [v["video_id"] for v in mock_context._database._videos]
        assert 2 not in video_ids
        assert 4 not in video_ids
        assert len(video_ids) == 3

    def test_delete_cancelled_by_user(self, qtbot, mock_context, monkeypatch):
        """Test that cancelling delete preserves videos."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        videos = make_video_dicts(5)
        mock_context._database._videos = videos

        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.show()
        qtbot.waitExposed(page)

        page.refresh()
        QApplication.processEvents()

        # Select a video
        page._selector.deselect_all()
        page._selector.include(1)
        page._selected_video_ids = {1}

        # Mock QMessageBox to reject deletion
        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *args, **kwargs: QMessageBox.StandardButton.No,
        )

        # Call delete
        page._delete_selected()

        # Video should still exist
        video_ids = [v["video_id"] for v in mock_context._database._videos]
        assert 1 in video_ids
        assert len(video_ids) == 5

    def test_delete_with_no_selection(self, qtbot, mock_context):
        """Test that delete does nothing when nothing is selected."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        videos = make_video_dicts(5)
        mock_context._database._videos = videos

        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.show()
        qtbot.waitExposed(page)

        page.refresh()
        QApplication.processEvents()

        # No selection
        page._selected_video_ids = set()
        page._selected_video_id = None

        # Call delete - should do nothing
        page._delete_selected()

        # All videos should still exist
        assert len(mock_context._database._videos) == 5


class TestVideoPropertyWidget:
    """Tests for single video property editing."""

    def test_set_video_property(self, qtbot, mock_context):
        """Test setting a property on a single video."""
        videos = make_video_dicts(3)
        videos[0]["properties"] = {"genre": ["action"]}
        mock_context._database._videos = videos

        # Set new property values
        mock_context._database.video_entry_set_tags(1, {"genre": ["comedy", "drama"]})

        # Verify change
        video = mock_context._database._get_video(1)
        assert video["properties"]["genre"] == ["comedy", "drama"]

    def test_set_multiple_properties(self, qtbot, mock_context):
        """Test setting multiple properties at once."""
        videos = make_video_dicts(3)
        videos[0]["properties"] = {"genre": ["action"], "rating": [5]}
        mock_context._database._videos = videos

        # Set multiple properties
        mock_context._database.video_entry_set_tags(
            1, {"genre": ["comedy"], "rating": [8], "year": [2024]}
        )

        # Verify changes
        video = mock_context._database._get_video(1)
        assert video["properties"]["genre"] == ["comedy"]
        assert video["properties"]["rating"] == [8]
        assert video["properties"]["year"] == [2024]
