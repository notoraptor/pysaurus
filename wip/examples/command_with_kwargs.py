import ast
import re
from typing import Tuple


def parse_command_with_kwargs(command_string: str) -> Tuple[str, dict]:
    # Extract command name
    cmd_parts = command_string.split(maxsplit=1)
    cmd_name = cmd_parts[0]
    args = {}

    if len(cmd_parts) > 1:
        # Parse arguments
        arg_pattern = re.compile(
            r'(\w+)=("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|\[.*?\]|\(.*?\)|\{.*?\}|[^ ]+)'
        )

        for key, value in arg_pattern.findall(cmd_parts[1]):
            try:
                # Convert to appropriate Python type
                args[key] = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                # Keep as string if conversion fails
                args[key] = value

    return cmd_name, args
