if __name__ == "__main__":
    import sys

    from pysaurus.core.functions import fatal
    from pysaurus.core.modules import System

    CEF = "cef"
    QT = "qt"
    GUIS = (CEF, QT)

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
        elif gui != QT:
            fatal(UnknownGUI(QT, gui))
    else:
        gui = CEF if System.is_windows() else QT
    if gui == CEF:
        from pysaurus.interface.cefgui.run import main
    else:  # assert gui == QT
        from pysaurus.interface.qtwebview.run import main
    main()
