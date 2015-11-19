import ast


def parse_named_values(query):
    values = {}
    def _eval(node):
        nonlocal values
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.NameConstant):
            return node.value

        elif isinstance(node, ast.Call):
            if len(node.args) != 2 and node.kwargs is not None:
                raise TypeError(node)
            if node.func.id == 'named_value':
                if not isinstance(node.args[0], ast.Str):
                    raise TypeError(node.args[0])
                values[node.args[0].s] = _eval(node.args[1])
            else:
                raise TypeError(node)
        elif isinstance(node, ast.Compare):
            if len(node.comparators) != 1 and len(node.ops) != 1:
                raise TypeError(node)
            _eval(node.left)
            _eval(node.comparators[0])
        elif isinstance(node, ast.BoolOp):
            _eval(node.values[0])
            _eval(node.values[1])

    _eval(ast.parse(query, mode='eval').body)
    return values
