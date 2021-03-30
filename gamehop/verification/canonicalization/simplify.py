import ast
import copy

def simplify(o: ast.AST) -> ast.AST:
    o = unary_operators(o)
    o = boolean_operators(o)
    return o

def unary_operators(o: ast.AST) -> ast.AST:
    """Modify (in place) the given AST object so that all unary operators
    applied to constants are simplified."""
    class UnarySimplifier(ast.NodeTransformer):
        def visit_UnaryOp(self, node):
            if not(isinstance(node.operand, ast.Constant)):
                node.operand = simplify(node.operand)
            if isinstance(node.operand, ast.Constant):
                if isinstance(node.op, ast.UAdd): return node.operand
                elif isinstance(node.op, ast.USub): return ast.Constant(-node.operand.value)
                elif isinstance(node.op, ast.Not): return ast.Constant(not(node.operand.value))
                elif isinstance(node.op, ast.Invert): return ast.Constant(~node.operand.value)
            else: return node
    o = UnarySimplifier().visit(o)
    ast.fix_missing_locations(o)
    return o

def boolean_operators(o: ast.AST) -> ast.AST:
    """Modify (in place) the given AST object so that all boolean operations
    applied to constants are simplified."""
    class BoolOpSimplifier(ast.NodeTransformer):
        def visit_BoolOp(self, node):
            for i in range(len(node.values)):
                if not(isinstance(node.values[i], ast.Constant)):
                    node.values[i] = simplify(node.values[i])
            all_constants = True
            for v in node.values:
                all_constants = all_constants and isinstance(v, ast.Constant)
            if all_constants:
                if isinstance(node.op, ast.And):
                    newv = True
                    for v in node.values: newv = newv and v.value
                    return ast.Constant(newv)
                elif isinstance(node.op, ast.Or):
                    newv = False
                    for v in node.values: newv = newv or v.value
                    return ast.Constant(newv)
            return node
    o = BoolOpSimplifier().visit(o)
    ast.fix_missing_locations(o)
    return o
