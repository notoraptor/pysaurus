import sys

try:
    sys.exit(1)
except SystemExit as exc:
    print("Exit", exc)
    print("Hwllo world")
