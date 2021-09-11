if __name__ == "__main__":
    import sys
    from pysaurus.core.modules import System

    if len(sys.argv) == 2:
        gui = sys.argv[1].strip().lower()
        if System.is_windows():
            if gui not in ("cef", "qt"):
                print(
                    f"Unknown interface on {System.platform()},",
                    "expected cef or qt, got",
                    gui,
                )
                exit(1)
        elif gui != "qt":
            print(f"Unknown interface on {System.platform()}, expected qt, got", gui)
            exit(1)
    elif System.is_windows():
        gui = "cef"
    else:
        gui = "qt"
    if gui == "cef":
        from pysaurus.interface.cefgui.run import main
    else:
        assert gui == "qt"
        from pysaurus.interface.qtwebview.run import main
    main()
