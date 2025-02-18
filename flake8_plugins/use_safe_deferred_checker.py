import ast
import re


class UseSafeDeferredChecker:
    name = "use-safe-deferred-checker"
    version = "0.0.1"
    ETBA1 = "ETBA2 '{}' is imported, but direct use of App Engine deferred is not allowed. Use backend.common.helpers.deferred instead."

    def __init__(self, tree, filename):
        self.tree = tree
        self.filename = filename

    def _is_allowed(self, i):
        """
        Disallow cross-service imports
        backend.common is allowed
        """
        x = re.search(r"src\/backend\/(.*)\/", self.filename)
        if not x:
            return True

        frm, imp, _ = i
        if frm == ["google", "appengine", "ext"] and imp == ["deferred"]:
            return False
        if frm == ["google", "appengine", "ext", "deferred"]:
            return False
        if imp == ["google", "appengine", "ext", "deferred"]:
            return False

        return True

    def _get_imports(self, node):
        if isinstance(node, ast.Import):
            module = []
        elif isinstance(node, ast.ImportFrom):
            module = node.module.split(".")
        else:
            return None

        return [(module, n.name.split("."), n.name) for n in node.names]

    def run(self):
        for node in ast.walk(self.tree):
            imports = self._get_imports(node)
            if imports:
                for i in imports:
                    if not self._is_allowed(i):
                        yield (
                            node.lineno,
                            node.col_offset,
                            self.ETBA1.format(i[2]),
                            type(self),
                        )
