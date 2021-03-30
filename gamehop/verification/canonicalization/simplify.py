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
            # recurse if the operand is not a constant
            if not(isinstance(node.operand, ast.Constant)): node.operand = simplify(node.operand)
            # if operand still not a constant, nothing we can do
            if not(isinstance(node.operand, ast.Constant)): return node
            # do replacements based on operator type
            if isinstance(node.op, ast.UAdd): return node.operand
            elif isinstance(node.op, ast.USub): return ast.Constant(-node.operand.value)
            elif isinstance(node.op, ast.Not): return ast.Constant(not(node.operand.value))
            elif isinstance(node.op, ast.Invert): return ast.Constant(~node.operand.value)
            assert False
    o = UnarySimplifier().visit(o)
    ast.fix_missing_locations(o)
    return o

def boolean_operators(o: ast.AST) -> ast.AST:
    """Modify (in place) the given AST object so that all boolean operations
    applied to constants are simplified."""
    class BoolOpSimplifier(ast.NodeTransformer):
        def visit_BoolOp(self, node):
            # recurse on all the operands if they are not constant
            for i in range(len(node.values)):
                if not(isinstance(node.values[i], ast.Constant)):
                    node.values[i] = simplify(node.values[i])
            # for and's, we can simplify if any node is False
            if isinstance(node.op, ast.And):
                for v in node.values:
                    if isinstance(v, ast.Constant) and v.value == False: return ast.Constant(False)
            # for or's, we can simplify if any node is True
            if isinstance(node.op, ast.Or):
                for v in node.values:
                    if isinstance(v, ast.Constant) and v.value == True: return ast.Constant(True)
            # we can also simplify if all nodes are constants
            all_constants = True
            for v in node.values: all_constants = all_constants and isinstance(v, ast.Constant)
            if all_constants:
                # if they're all constants, and it's an and, then we know that none of the constants is False
                # (otherwise it would have returned above), so they must all be True
                if isinstance(node.op, ast.And): return ast.Constant(True)
                # if they're all constants, and it's an or, then we know that none of the constants is True
                # (otherwise it would have returned above), so they must all be False
                if isinstance(node.op, ast.Or): return ast.Constant(False)
                assert False
            else: return node
    o = BoolOpSimplifier().visit(o)
    ast.fix_missing_locations(o)
    return o
