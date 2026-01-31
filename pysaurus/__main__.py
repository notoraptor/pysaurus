if __name__ == "__main__":
    import sys

    from pysaurus.core.functions import fatal
    from pysaurus.core.modules import System

    PYWEBVIEW = "pywebview"
    QT = "qt"
    PYSIDE6 = "pyside6"
    GUIS = (PYWEBVIEW, QT, PYSIDE6)

    class UnknownGUI(Exception):
        def __init__(self, expected, given):
            self.platform = System.platform()
            self.expected = expected
            self.given = given

    if len(sys.argv) == 2:
        gui = sys.argv[1].strip().lower()
        if System.is_windows():
            if gui not in GUIS:
                fatal(UnknownGUI(GUIS, gui))
        elif gui not in (QT, PYSIDE6):
            fatal(UnknownGUI((QT, PYSIDE6), gui))
    else:
        gui = PYWEBVIEW if System.is_windows() else QT
    if gui == PYWEBVIEW:
        from pysaurus.interface.using_pywebview.webview_app import main
    elif gui == PYSIDE6:
        from pysaurus.interface.pyside6.main import main
    else:  # assert gui == QT
        from pysaurus.interface.qtwebview.run import main
    main()
