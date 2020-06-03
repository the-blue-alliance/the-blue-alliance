import ast
import re


class ServiceImportChecker:
    name = "service-import-checker"
    version = "0.0.1"
    ETBA0 = "ETBA0 '{}' is imported, but cross-service imports are not allowed"

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

        service = x.group(1).split("/")[0]

        frm, imp, _ = i
        if frm == ["backend"]:
            return False
        if frm and frm[0] == "backend" and frm[1] not in {service, "common"}:
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
                            self.ETBA0.format(i[2]),
                            type(self),
                        )
