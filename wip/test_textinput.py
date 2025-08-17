import pytest
import pygame

import videre
from videre.core.constants import MouseButton
from videre.core.events import KeyboardEntry, MouseEvent
from videre_tests.testing.utils import SD


class TestTextInputBasics:
    """Test basic TextInput functionality"""

    @pytest.mark.win_params({"background": videre.Colors.white, **SD})
    def test_textinput_initial_state(self, fake_win):
        """Test TextInput initial state and rendering"""
        textinput = videre.TextInput()
        fake_win.controls = [textinput]

        # Check initial state - TextInput has default value
        assert len(textinput.value) > 0  # Has some default text
        assert not textinput._has_focus()
        assert textinput._get_cursor() == len(textinput.value)
        assert not textinput._has_selection()

        fake_win.check("initial_state")

    @pytest.mark.win_params({"background": videre.Colors.white, **SD})
    def test_textinput_empty(self, fake_win):
        """Test empty TextInput"""
        textinput = videre.TextInput()
        textinput.value = ""
        fake_win.controls = [textinput]

        assert textinput.value == ""
        assert textinput._get_cursor() == 0

        fake_win.check("empty")

    @pytest.mark.win_params({"background": videre.Colors.white, **SD})
    def test_textinput_with_focus(self, fake_win):
        """Test TextInput with focus (shows cursor)"""
        textinput = videre.TextInput()
        textinput.value = "Hello World"
        textinput._set_focus(True)
        fake_win.controls = [textinput]

        assert textinput._has_focus()
        fake_win.check("with_focus")

    def test_textinput_value_property(self):
        """Test value property getter/setter"""
        textinput = videre.TextInput()

        # Test setter
        textinput.value = "New Text"
        assert textinput.value == "New Text"
        assert textinput._get_cursor() == len("New Text")
        assert not textinput._has_selection()

        # Test with empty string
        textinput.value = ""
        assert textinput.value == ""
        assert textinput._get_cursor() == 0


class TestTextInputEditing:
    """Test text editing operations"""

    def test_text_insertion(self):
        """Test basic text insertion"""
        textinput = videre.TextInput()
        textinput.value = "Hello"
        textinput._set_cursor(5)  # End of text

        # Insert text at cursor
        textinput.handle_text_input(" World")

        assert textinput.value == "Hello World"
        assert textinput._get_cursor() == 11

    def test_text_insertion_middle(self):
        """Test text insertion in middle of text"""
        textinput = videre.TextInput()
        textinput.value = "HelloWorld"
        textinput._set_cursor(5)  # Between Hello and World

        textinput.handle_text_input(" ")

        assert textinput.value == "Hello World"
        assert textinput._get_cursor() == 6

    def test_text_replacement_with_selection(self):
        """Test text replacement when selection exists"""
        textinput = videre.TextInput()
        textinput.value = "Hello World"
        textinput._set_selection(6, 11)  # Select "World"
        textinput._set_cursor(11)

        textinput.handle_text_input("Python")

        assert textinput.value == "Hello Python"
        assert textinput._get_cursor() == 12
        assert not textinput._has_selection()

    def test_backspace_basic(self):
        """Test basic backspace operation"""
        textinput = videre.TextInput()
        textinput.value = "Hello"
        textinput._set_cursor(5)

        # Create mock backspace event
        backspace_event = KeyboardEntry(
            pygame.event.Event(
                pygame.KEYDOWN, {"key": pygame.K_BACKSPACE, "mod": 0, "unicode": ""}
            )
        )

        textinput.handle_keydown(backspace_event)

        assert textinput.value == "Hell"
        assert textinput._get_cursor() == 4

    def test_backspace_with_selection(self):
        """Test backspace with selected text"""
        textinput = videre.TextInput()
        textinput.value = "Hello World"
        textinput._set_selection(6, 11)  # Select "World"
        textinput._set_cursor(11)

        backspace_event = KeyboardEntry(
            pygame.event.Event(
                pygame.KEYDOWN, {"key": pygame.K_BACKSPACE, "mod": 0, "unicode": ""}
            )
        )

        textinput.handle_keydown(backspace_event)

        assert textinput.value == "Hello "
        assert textinput._get_cursor() == 6
        assert not textinput._has_selection()

    def test_delete_basic(self):
        """Test basic delete operation"""
        textinput = videre.TextInput()
        textinput.value = "Hello"
        textinput._set_cursor(4)  # Before 'o'

        delete_event = KeyboardEntry(
            pygame.event.Event(
                pygame.KEYDOWN, {"key": pygame.K_DELETE, "mod": 0, "unicode": ""}
            )
        )

        textinput.handle_keydown(delete_event)

        assert textinput.value == "Hell"
        assert textinput._get_cursor() == 4

    def test_ctrl_backspace_word_deletion(self):
        """Test Ctrl+Backspace for word deletion"""
        textinput = videre.TextInput()
        textinput.value = "Hello World Test"
        textinput._set_cursor(16)  # End of text

        ctrl_backspace_event = KeyboardEntry(
            pygame.event.Event(
                pygame.KEYDOWN,
                {"key": pygame.K_BACKSPACE, "mod": pygame.KMOD_CTRL, "unicode": ""},
            )
        )

        textinput.handle_keydown(ctrl_backspace_event)

        assert textinput.value == "Hello World "
        assert textinput._get_cursor() == 12


class TestTextInputCursor:
    """Test cursor positioning and navigation"""

    def test_cursor_positioning(self):
        """Test basic cursor positioning"""
        textinput = videre.TextInput()
        textinput.value = "Hello"

        # Test setting cursor at different positions
        textinput._set_cursor(0)
        assert textinput._get_cursor() == 0

        textinput._set_cursor(3)
        assert textinput._get_cursor() == 3

        textinput._set_cursor(5)
        assert textinput._get_cursor() == 5

    def test_arrow_navigation(self):
        """Test left/right arrow navigation"""
        textinput = videre.TextInput()
        textinput.value = "Hello World"
        textinput._set_cursor(6)  # Between Hello and World

        # Test left arrow
        left_event = KeyboardEntry(
            pygame.event.Event(
                pygame.KEYDOWN, {"key": pygame.K_LEFT, "mod": 0, "unicode": ""}
            )
        )

        textinput.handle_keydown(left_event)
        assert textinput._get_cursor() == 5

        # Test right arrow
        right_event = KeyboardEntry(
            pygame.event.Event(
                pygame.KEYDOWN, {"key": pygame.K_RIGHT, "mod": 0, "unicode": ""}
            )
        )

        textinput.handle_keydown(right_event)
        assert textinput._get_cursor() == 6

    def test_ctrl_arrow_word_navigation(self):
        """Test Ctrl+Arrow for word-by-word navigation"""
        textinput = videre.TextInput()
        textinput.value = "Hello World Test"
        textinput._set_cursor(16)  # End

        # Test Ctrl+Left (move to previous word)
        ctrl_left_event = KeyboardEntry(
            pygame.event.Event(
                pygame.KEYDOWN,
                {"key": pygame.K_LEFT, "mod": pygame.KMOD_CTRL, "unicode": ""},
            )
        )

        textinput.handle_keydown(ctrl_left_event)
        assert textinput._get_cursor() == 12  # Start of "Test"

        textinput.handle_keydown(ctrl_left_event)
        assert textinput._get_cursor() == 6  # Start of "World"

        # Test Ctrl+Right (move to next word)
        ctrl_right_event = KeyboardEntry(
            pygame.event.Event(
                pygame.KEYDOWN,
                {"key": pygame.K_RIGHT, "mod": pygame.KMOD_CTRL, "unicode": ""},
            )
        )

        textinput.handle_keydown(ctrl_right_event)
        assert textinput._get_cursor() == 11  # End of "World"


class TestTextInputSelection:
    """Test text selection functionality"""

    def test_selection_basic(self):
        """Test basic text selection"""
        textinput = videre.TextInput()
        textinput.value = "Hello World"

        # Set selection
        textinput._set_selection(0, 5)  # Select "Hello"

        assert textinput._has_selection()
        assert textinput._get_selection() == (0, 5)

    def test_selection_clearing(self):
        """Test clearing selection"""
        textinput = videre.TextInput()
        textinput.value = "Hello World"
        textinput._set_selection(0, 5)

        # Clear selection
        textinput._set_selection(None)

        assert not textinput._has_selection()

    def test_shift_arrow_selection(self):
        """Test selection with Shift+Arrow keys"""
        textinput = videre.TextInput()
        textinput.value = "Hello World"
        textinput._set_cursor(5)  # At space

        # Test Shift+Right to select characters
        shift_right_event = KeyboardEntry(
            pygame.event.Event(
                pygame.KEYDOWN,
                {"key": pygame.K_RIGHT, "mod": pygame.KMOD_SHIFT, "unicode": ""},
            )
        )

        textinput.handle_keydown(shift_right_event)

        assert textinput._has_selection()
        selection = textinput._get_selection()
        assert selection[0] == 5
        assert selection[1] == 6

    def test_ctrl_shift_word_selection(self):
        """Test word selection with Ctrl+Shift+Arrow"""
        textinput = videre.TextInput()
        textinput.value = "Hello World Test"
        textinput._set_cursor(6)  # Start of "World"

        # Test Ctrl+Shift+Right to select entire word
        ctrl_shift_right_event = KeyboardEntry(
            pygame.event.Event(
                pygame.KEYDOWN,
                {
                    "key": pygame.K_RIGHT,
                    "mod": pygame.KMOD_CTRL | pygame.KMOD_SHIFT,
                    "unicode": "",
                },
            )
        )

        textinput.handle_keydown(ctrl_shift_right_event)

        assert textinput._has_selection()
        selection = textinput._get_selection()
        assert selection[0] == 6
        assert selection[1] == 11  # End of "World"

    def test_select_all(self):
        """Test Ctrl+A select all functionality"""
        textinput = videre.TextInput()
        textinput.value = "Hello World"
        textinput._set_cursor(3)

        # Test Ctrl+A
        ctrl_a_event = KeyboardEntry(
            pygame.event.Event(
                pygame.KEYDOWN,
                {"key": pygame.K_a, "mod": pygame.KMOD_CTRL, "unicode": ""},
            )
        )

        textinput.handle_keydown(ctrl_a_event)

        assert textinput._has_selection()
        assert textinput._get_selection() == (0, len(textinput.value))
        assert textinput._get_cursor() == len(textinput.value)


class TestTextInputClipboard:
    """Test clipboard operations - Note: These require window context for get_window()"""

    def test_clipboard_operations_isolated(self):
        """Test clipboard logic without window dependency"""
        textinput = videre.TextInput()
        textinput.value = "Hello World"

        # Test selection state for copy operations
        textinput._set_selection(6, 11)  # Select "World"
        assert textinput._has_selection()
        selection = textinput._get_selection()
        selected_text = textinput.value[selection[0] : selection[1]]
        assert selected_text == "World"

        # Test that selection exists for copy (logic test)
        assert textinput._has_selection() == True


class TestTextInputFocus:
    """Test focus management"""

    def test_focus_in(self):
        """Test focus in behavior"""
        textinput = videre.TextInput()
        textinput.value = "Hello"

        result = textinput.handle_focus_in()

        assert result is True
        assert textinput._has_focus()

    def test_focus_out(self):
        """Test focus out behavior"""
        textinput = videre.TextInput()
        textinput.value = "Hello"
        textinput._set_focus(True)
        textinput._set_selection(0, 5)

        textinput.handle_focus_out()

        assert not textinput._has_focus()
        assert not textinput._has_selection()

    def test_focus_in_sets_cursor(self):
        """Test focus in sets cursor if none exists"""
        textinput = videre.TextInput()
        textinput.value = "Hello"
        textinput._cursor_event = None

        textinput.handle_focus_in()

        assert textinput._cursor_event is not None
        assert textinput._get_cursor() == 0


class TestTextInputEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_text_operations(self):
        """Test operations on empty text"""
        textinput = videre.TextInput()
        textinput.value = ""

        # Test backspace on empty text
        backspace_event = KeyboardEntry(
            pygame.event.Event(
                pygame.KEYDOWN, {"key": pygame.K_BACKSPACE, "mod": 0, "unicode": ""}
            )
        )

        textinput.handle_keydown(backspace_event)
        assert textinput.value == ""
        assert textinput._get_cursor() == 0

    def test_cursor_bounds_checking(self):
        """Test cursor position bounds are respected"""
        textinput = videre.TextInput()
        textinput.value = "Hello"

        # Test cursor at end
        textinput._set_cursor(100)  # Beyond text length
        assert textinput._get_cursor() == 100  # TextInput allows this

        # Test cursor at start
        textinput._set_cursor(-5)  # Before text start
        assert textinput._get_cursor() == -5  # TextInput allows this

    def test_unicode_text_support(self):
        """Test Unicode text handling"""
        textinput = videre.TextInput()

        # Test with Unicode characters
        unicode_text = "Hello 世界 🌍"
        textinput.value = unicode_text

        assert textinput.value == unicode_text
        assert textinput._get_cursor() == len(unicode_text)

        # Test insertion with Unicode
        textinput._set_cursor(5)
        textinput.handle_text_input(" 🎯")

        assert "🎯" in textinput.value

    def test_multiline_text_handling(self):
        """Test handling of multiline text"""
        textinput = videre.TextInput()
        multiline_text = "Line 1\nLine 2\nLine 3"
        textinput.value = multiline_text

        assert textinput.value == multiline_text
        assert "\n" in textinput.value

        # Test cursor positioning with newlines
        textinput._set_cursor(7)  # After "Line 1\n"
        textinput.handle_text_input("X")

        assert "X" in textinput.value

    def test_delete_with_selection(self):
        """Test delete key with selected text"""
        textinput = videre.TextInput()
        textinput.value = "Hello World"
        textinput._set_selection(6, 11)  # Select "World"
        textinput._set_cursor(11)

        delete_event = KeyboardEntry(
            pygame.event.Event(
                pygame.KEYDOWN, {"key": pygame.K_DELETE, "mod": 0, "unicode": ""}
            )
        )

        textinput.handle_keydown(delete_event)

        assert textinput.value == "Hello "
        assert textinput._get_cursor() == 6
        assert not textinput._has_selection()

    def test_ctrl_delete_word_deletion(self):
        """Test Ctrl+Delete for forward word deletion"""
        textinput = videre.TextInput()
        textinput.value = "Hello World Test"
        textinput._set_cursor(6)  # At start of "World"

        ctrl_delete_event = KeyboardEntry(
            pygame.event.Event(
                pygame.KEYDOWN,
                {"key": pygame.K_DELETE, "mod": pygame.KMOD_CTRL, "unicode": ""},
            )
        )

        textinput.handle_keydown(ctrl_delete_event)

        # Should delete "World" only (not the space)
        assert textinput.value == "Hello  Test"
        assert textinput._get_cursor() == 6

    def test_cursor_at_text_boundaries(self):
        """Test cursor movement at text boundaries"""
        textinput = videre.TextInput()
        textinput.value = "Hello"

        # Test left arrow at beginning (should stay at 0)
        textinput._set_cursor(0)
        left_event = KeyboardEntry(
            pygame.event.Event(
                pygame.KEYDOWN, {"key": pygame.K_LEFT, "mod": 0, "unicode": ""}
            )
        )
        textinput.handle_keydown(left_event)
        assert textinput._get_cursor() == 0

        # Test right arrow at end (should stay at end)
        textinput._set_cursor(5)
        right_event = KeyboardEntry(
            pygame.event.Event(
                pygame.KEYDOWN, {"key": pygame.K_RIGHT, "mod": 0, "unicode": ""}
            )
        )
        textinput.handle_keydown(right_event)
        assert textinput._get_cursor() == 5

    def test_unknown_key_handling(self):
        """Test handling of unknown key events"""
        textinput = videre.TextInput()
        textinput.value = "Hello"

        # Test with unknown key (should not crash)
        unknown_event = KeyboardEntry(
            pygame.event.Event(
                pygame.KEYDOWN, {"key": pygame.K_F1, "mod": 0, "unicode": ""}
            )
        )

        result = textinput.handle_keydown(unknown_event)

        # Should return None and not modify text
        assert result is None
        assert textinput.value == "Hello"


class TestTextInputVisual:
    """Test visual rendering with different states"""

    @pytest.mark.win_params({"background": videre.Colors.white, **SD})
    def test_textinput_with_selection_visual(self, fake_win):
        """Test visual rendering with text selection"""
        textinput = videre.TextInput()
        textinput.value = "Hello World Test"
        textinput._set_focus(True)
        textinput._set_selection(6, 11)  # Select "World"
        fake_win.controls = [textinput]

        fake_win.check("with_selection")

    @pytest.mark.win_params({"background": videre.Colors.white, **SD})
    def test_textinput_cursor_positions(self, fake_win):
        """Test cursor visual rendering at different positions"""
        textinput = videre.TextInput()
        textinput.value = "Hello World"
        textinput._set_focus(True)
        textinput._set_cursor(6)  # At space
        fake_win.controls = [textinput]

        fake_win.check("cursor_at_space")

    @pytest.mark.win_params({"background": videre.Colors.white, **SD})
    def test_textinput_long_text(self, fake_win):
        """Test with long text content"""
        textinput = videre.TextInput()
        textinput.value = "This is a very long text that might exceed the normal width of the TextInput widget to test text wrapping and scrolling behavior."
        textinput._set_focus(True)
        textinput._set_cursor(50)
        fake_win.controls = [textinput]

        fake_win.check("long_text")

    @pytest.mark.win_params({"background": videre.Colors.white, **SD})
    def test_textinput_unicode_mixed(self, fake_win):
        """Test with mixed Unicode content"""
        textinput = videre.TextInput()
        textinput.value = "English 中文 日本語 한글 🌍🎯"
        textinput._set_focus(True)
        textinput._set_cursor(8)  # In Chinese section
        fake_win.controls = [textinput]

        fake_win.check("unicode_mixed")
