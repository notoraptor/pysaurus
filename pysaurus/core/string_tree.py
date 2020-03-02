from typing import Dict

def _get_common_prefix(a: str, b: str):
    # a and be should be non-None non-empty strings.
    common_len = min(len(a), len(b))
    for i in range(common_len):
        if a[i] != b[i]:
            return a[:i]
    return a[:common_len]


class StringTreeNode:
    def __init__(self):
        self.value = None
        self.children = {}  # type: Dict[str, StringTreeNode]
        self.terminal = False

    def add(self, string: str):
        assert string, 'StringTreeNode: cannot add None or empty strings.'
        if self.value is None:
            # This node should be a root not yet set.
            assert not self.children
            self.value = string
            self.terminal = True
            return True
        elif self.value == '':
            # This node has divergent children with no common prefix.
            return self.add_child(string)
        else:
            string_prefix = _get_common_prefix(self.value, string)
            string_suffix = string[len(string_prefix):]
            if string_prefix:
                len_string_prefix = len(string_prefix)
                len_value = len(self.value)
                if len_string_prefix < len_value:
                    value_suffix = self.value[len_string_prefix:]
                    new_node = StringTreeNode()
                    new_node.value = value_suffix
                    new_node.children = self.children
                    new_node.terminal = self.terminal
                    self.value = string_prefix
                    self.children = {new_node.value: new_node}
                    self.terminal = False
                    if string_suffix:
                        other_node = StringTreeNode()
                        other_node.value = string_suffix
                        other_node.terminal = True
                        self.children[other_node.value] = other_node
                    else:
                        self.terminal = True
                elif len_string_prefix == len_value:
                    if string_suffix:
                        self.add_child(string_suffix)
                    else:
                        self.terminal = True
                # Otherwise, prefix cannot be longer than value, as it's a prefix!
                return True
            # If no prefix, then we cannot add this string here, it should be added to node parent, if exists!
        return False

    def add_child(self, string: str):
        previous_value = None
        target = None
        for child in self.children.values():  # type: StringTreeNode
            previous_value = child.value
            if child.add(string):
                target = child
                break
        if target:
            if previous_value != target.value:
                del self.children[previous_value]
                if target.value in self.children:
                    self.children[target.value].merge(target)
                else:
                    self.children[target.value] = target
        else:
            # Add a new child.
            new_node = StringTreeNode()
            new_node.value = string
            new_node.terminal = True
            self.children[new_node.value] = new_node
        return True

    def merge(self, other):
        # type: (StringTreeNode) -> None
        assert self.value == other.value
        self.terminal = self.terminal or other.terminal
        for other_child in other.children.values():
            if other_child.value in self.children:
                self.children[other_child.value].merge(other_child)
            else:
                self.children[other_child.value] = other_child

    def debug(self, prefix=''):
        print('%s[%s%d] %s' % (prefix, ('TERMINAL ' if self.terminal else ''), len(self.children), self.value))
        for child_value in sorted(self.children):
            self.children[child_value].debug(prefix + '\t')


class StringTree:
    def __init__(self):
        self.root = StringTreeNode()
        self.root.value = ''

    def add(self, string: str):
        self.root.add(string)
        # self.debug()

    def debug(self):
        self.root.debug()


if __name__ == '__main__':
    t = StringTree()
    t.add('bonjour')
    t.add('bonjour, comment vas-tu?')
    t.add('bonjour, ça va')
    t.add('bonjour, ça va bien')
    t.add('bonjour, ça va bien!')
    t.add('bonjour, ça va, et toi?')
    t.add('bonjour, ça va bien, merci!')
    t.debug()
