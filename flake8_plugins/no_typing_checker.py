import ast


class NoTypingChecker:
    name = "no-anystr-checker"
    version = "0.0.1"

    DEPRECATED_IMPORTS = {
        "AnyStr": "ETBA3 Do not import 'AnyStr' from 'typing' - use 'str | bytes' instead",
        "Optional": "ETBA3 Do not import 'Optional' from 'typing' - use 'X | None' instead",
        "Dict": "ETBA3 Do not import 'Dict' from 'typing' - use 'dict' instead",
        "List": "ETBA3 Do not import 'List' from 'typing' - use 'list' instead",
        "Union": "ETBA3 Do not import 'Union' from 'typing' - use 'X | Y' instead",
        "Tuple": "ETBA3 Do not import 'Tuple' from 'typing' - use 'tuple' instead",
        "DefaultDict": "ETBA3 Do not import 'DefaultDict' from 'typing' - use 'collections.defaultdict' instead",
    }

    def __init__(self, tree, filename):
        self.tree = tree
        self.filename = filename

    def run(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "typing":
                    for alias in node.names:
                        if alias.name in self.DEPRECATED_IMPORTS:
                            yield (
                                node.lineno,
                                node.col_offset,
                                self.DEPRECATED_IMPORTS[alias.name],
                                type(self),
                            )
