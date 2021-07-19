from pysaurus.core.testing import TEST_LIST_FILE_PATH
from pysaurus.interface.console.command_line_interface import command_line_interface
from pysaurus.interface.console.console_parser import ConsoleParser


def main():
    command_line_interface(ConsoleParser(TEST_LIST_FILE_PATH))


if __name__ == '__main__':
    main()
