if __name__ == "__main__":
    import sys

    from pysaurus.core.functions import fatal
    from pysaurus.core.modules import System

    PYWEBVIEW = "pywebview"
    QTWEBVIEW = "qtwebview"
    PYSIDE6 = "pyside6"
    GUIS = (PYWEBVIEW, QTWEBVIEW, PYSIDE6)

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
    elif gui == PYSIDE6:
        from pysaurus.interface.pyside6.main import main
    else:  # assert gui == QT
        from pysaurus.interface.qtwebview.run import main
    main()
