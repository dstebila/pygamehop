import ast
import copy

def simplify(o: ast.AST) -> ast.AST:
    o = unary_operators(o)
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
