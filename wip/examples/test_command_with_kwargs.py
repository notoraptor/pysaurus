from wip.examples.command_with_kwargs import parse_command_with_kwargs


def test_command_only():
    """Test with only a command name without arguments."""
    cmd = "macommande"
    cmd_name, args = parse_command_with_kwargs(cmd)
    assert cmd_name == "macommande"
    assert args == {}


def test_string_arguments():
    """Test with string type arguments."""
    cmd = 'command_name arg1="hello world" arg2="autre chaîne"'
    cmd_name, args = parse_command_with_kwargs(cmd)
    assert cmd_name == "command_name"
    assert args["arg1"] == "hello world"
    assert args["arg2"] == "autre chaîne"
    assert isinstance(args["arg1"], str)
    assert isinstance(args["arg2"], str)


def test_numeric_arguments():
    """Test with numeric arguments (integers and floats)."""
    cmd = "command_name arg1=123 arg2=456.789 arg3=123.456e10"
    cmd_name, args = parse_command_with_kwargs(cmd)
    assert cmd_name == "command_name"
    assert args["arg1"] == 123
    assert args["arg2"] == 456.789
    assert args["arg3"] == 123.456e10
    assert isinstance(args["arg1"], int)
    assert isinstance(args["arg2"], float)
    assert isinstance(args["arg3"], float)


def test_boolean_arguments():
    """Test with boolean arguments."""
    cmd = "command_name arg1=True arg2=False"
    cmd_name, args = parse_command_with_kwargs(cmd)
    assert cmd_name == "command_name"
    assert args["arg1"] is True
    assert args["arg2"] is False
    assert isinstance(args["arg1"], bool)
    assert isinstance(args["arg2"], bool)


def test_none_argument():
    """Test with a None argument."""
    cmd = "command_name arg1=None"
    cmd_name, args = parse_command_with_kwargs(cmd)
    assert cmd_name == "command_name"
    assert args["arg1"] is None


def test_list_arguments():
    """Test with list type arguments."""
    cmd = 'command_name arg1=[1, 2, 3] arg2=["a", "b", "c"]'
    cmd_name, args = parse_command_with_kwargs(cmd)
    assert cmd_name == "command_name"
    assert args["arg1"] == [1, 2, 3]
    assert args["arg2"] == ["a", "b", "c"]
    assert isinstance(args["arg1"], list)
    assert isinstance(args["arg2"], list)


def test_tuple_arguments():
    """Test with tuple type arguments."""
    cmd = 'command_name arg1=(1, 2, 3) arg2=("a", "b", "c")'
    cmd_name, args = parse_command_with_kwargs(cmd)
    assert cmd_name == "command_name"
    assert args["arg1"] == (1, 2, 3)
    assert args["arg2"] == ("a", "b", "c")
    assert isinstance(args["arg1"], tuple)
    assert isinstance(args["arg2"], tuple)


def test_mixed_arguments():
    """Test with different mixed argument types."""
    cmd = 'command_name arg1="string" arg2=123 arg3=True arg4=[1, 2, 3] arg5=(4, 5, 6) arg6=None'
    cmd_name, args = parse_command_with_kwargs(cmd)
    assert cmd_name == "command_name"
    assert args["arg1"] == "string"
    assert args["arg2"] == 123
    assert args["arg3"] is True
    assert args["arg4"] == [1, 2, 3]
    assert args["arg5"] == (4, 5, 6)
    assert args["arg6"] is None
    assert isinstance(args["arg1"], str)
    assert isinstance(args["arg2"], int)
    assert isinstance(args["arg3"], bool)
    assert isinstance(args["arg4"], list)
    assert isinstance(args["arg5"], tuple)


def test_escaped_quotes():
    """Test with escaped quotes in strings."""
    cmd = "command_name arg1=\"chaîne avec \\\"guillemets\\\"\" arg2='autre avec \\'apostrophes\\''"
    cmd_name, args = parse_command_with_kwargs(cmd)
    assert cmd_name == "command_name"
    assert len(args) == 2, args
    assert args["arg1"] == 'chaîne avec "guillemets"'
    assert args["arg2"] == "autre avec 'apostrophes'"


def test_unconvertible_values():
    """Test with values that literal_eval cannot convert."""
    cmd = "command_name arg1=variable_name arg2=fonction()"
    cmd_name, args = parse_command_with_kwargs(cmd)
    assert cmd_name == "command_name"
    assert args["arg1"] == "variable_name"
    assert args["arg2"] == "fonction()"
    assert isinstance(args["arg1"], str)
    assert isinstance(args["arg2"], str)


def test_empty_list_tuple():
    """Test with empty lists and tuples."""
    cmd = "command_name arg1=[] arg2=()"
    cmd_name, args = parse_command_with_kwargs(cmd)
    assert cmd_name == "command_name"
    assert args["arg1"] == []
    assert args["arg2"] == ()
    assert isinstance(args["arg1"], list)
    assert isinstance(args["arg2"], tuple)


def test_special_characters_in_string():
    """Test with special characters in strings."""
    cmd = r'command_name arg1="!@#$%^&*()\n\t" arg2="ligne 1\nligne 2"'
    cmd_name, args = parse_command_with_kwargs(cmd)
    assert cmd_name == "command_name"
    assert args["arg1"] == "!@#$%^&*()\n\t"
    assert args["arg2"] == "ligne 1\nligne 2"


def test_negative_numbers():
    """Test with negative numbers."""
    cmd = "command_name arg1=-123 arg2=-456.789 arg3=-1.23e-4"
    cmd_name, args = parse_command_with_kwargs(cmd)
    assert cmd_name == "command_name"
    assert args["arg1"] == -123
    assert args["arg2"] == -456.789
    assert args["arg3"] == -1.23e-4
    assert isinstance(args["arg1"], int)
    assert isinstance(args["arg2"], float)
    assert isinstance(args["arg3"], float)


def test_nested_structures():
    """Test with nested structures."""
    cmd = 'command_name arg1=[(1, 2), (3, 4)] arg2={"a": 1, "b": 2}'
    cmd_name, args = parse_command_with_kwargs(cmd)
    assert cmd_name == "command_name"
    assert args["arg1"] == [(1, 2), (3, 4)]
    assert args["arg2"] == {"a": 1, "b": 2}
    assert isinstance(args["arg1"], list)
    assert isinstance(args["arg2"], dict)


def test_whitespace_handling():
    """Test with different whitespace characters."""
    cmd = '  command_name   arg1=123   arg2="test"   '
    cmd_name, args = parse_command_with_kwargs(cmd)
    assert cmd_name == "command_name"
    assert args["arg1"] == 123
    assert args["arg2"] == "test"
