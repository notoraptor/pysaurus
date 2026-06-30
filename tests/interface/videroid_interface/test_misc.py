"""Coverage for the base Page default and the run_with_videroid entry point."""

from unittest.mock import Mock

import videre

from pysaurus.interface.videroid.pages.base_page import Page


class TestBasePage:
    def test_default_build_is_cached(self):
        page = Page(Mock())
        widget = page.get_widget()
        assert isinstance(widget, videre.Text)  # "(not implemented yet)" placeholder
        assert page.get_widget() is widget  # built once, cached
        page.on_show()  # default no-op hooks must not raise
        page.on_notification(Mock())


class TestRunWithVideroid:
    def test_main_runs_app_inside_information(self, monkeypatch):
        from pysaurus.interface.videroid import run_with_videroid as mod

        events = []

        class _Information:
            def __enter__(self):
                events.append("enter")
                return self

            def __exit__(self, *args):
                events.append("exit")
                return False

        app = Mock()
        app.run.return_value = 0
        monkeypatch.setattr(mod, "Information", _Information)
        monkeypatch.setattr(mod, "VideroidApp", lambda *a, **k: app)
        monkeypatch.setattr(
            mod.sys, "exit", lambda code: events.append(("exit_code", code))
        )

        mod.main()

        assert events[0] == "enter"  # app built inside the Information context
        app.run.assert_called_once()
        assert ("exit_code", 0) in events
