if __name__ == "__main__":
    import sys

    from pysaurus.core.functions import fatal
    from pysaurus.core.modules import System

    PYWEBVIEW = "pywebview"
    QTWEBVIEW = "qtwebview"
    PYSIDE6 = "pyside6"
    FLASK = "flask"
    FLASKVIEW = "flaskview"
    GUIS = (PYWEBVIEW, QTWEBVIEW, PYSIDE6, FLASK, FLASKVIEW)

    class UnknownGUI(Exception):
        def __init__(self, expected, given):
            self.platform = System.platform()
            self.expected = expected
            self.given = given

    if len(sys.argv) == 2:
        gui = sys.argv[1].strip().lower()
        if gui not in GUIS:
            fatal(UnknownGUI(GUIS, gui))
    else:
        gui = PYSIDE6

    if gui == PYWEBVIEW:
        from pysaurus.interface.using_pywebview.webview_app import main
    elif gui == FLASK:
        from pysaurus.interface.flask.main import main
    elif gui == FLASKVIEW:
        from pysaurus.interface.flask.main import main_desktop as main
    elif gui == PYSIDE6:
        from pysaurus.interface.pyside6.main import main
    else:  # assert gui == QTWEBVIEW
        from pysaurus.interface.qtwebview.run import main
    main()
