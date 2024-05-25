import ast


class APIAuthenticatedDecoratorCheker:
    name = "api-authenticated-decorator-checker"
    version = "0.0.1"
    ETBA1 = "ETBA1 'api_authenticated' must be the first decorator, but is after: {}"

    def __init__(self, tree, filename):
        self.tree = tree
        self.filename = filename

    def run(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                decorator_names = [
                    d.id if hasattr(d, "id") else None for d in node.decorator_list
                ]
                for i, name in enumerate(decorator_names):
                    if name == "api_authenticated" and i != 0:
                        yield (
                            node.lineno,
                            node.col_offset,
                            self.ETBA1.format(", ".join(decorator_names[:i])),
                            type(self),
                        )
