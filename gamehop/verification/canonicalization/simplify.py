import ast
import copy

def simplify(f: ast.FunctionDef) -> None:
    """Modify (in place) the given function definition so that all expressions
    involving constants are simplified."""
    # go through each statement in the body
    newbody = list()
    for stmt in f.body:
        newbody.append(simplify_internal(stmt))
    f.body = newbody
    ast.fix_missing_locations(f)

def simplify_internal(o: ast.stmt) -> ast.stmt:
    o = unary_operators(o)
    o = boolean_operators(o)
    o = binary_operators(o)
    return o

def unary_operators(o: ast.stmt) -> ast.stmt:
    """Modify the given AST object so that all unary operators
    applied to constants are simplified."""
    class UnarySimplifier(ast.NodeTransformer):
        def visit_UnaryOp(self, node):
            # recurse if the operand is not a constant
            if not(isinstance(node.operand, ast.Constant)): node.operand = simplify_internal(node.operand)
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

def boolean_operators(o: ast.stmt) -> ast.stmt:
    """Modify the given AST object so that all boolean operations
    applied to constants are simplified."""
    class BoolOpSimplifier(ast.NodeTransformer):
        def visit_BoolOp(self, node):
            # recurse on all the operands if they are not constant
            for i in range(len(node.values)):
                if not(isinstance(node.values[i], ast.Constant)):
                    node.values[i] = simplify_internal(node.values[i])
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

def binary_operators(o: ast.stmt) -> ast.stmt:
    """Modify the given AST object so that all binary operations
    applied to constants are simplified."""
    class BinOpSimplifier(ast.NodeTransformer):
        def visit_BinOp(self, node):
            # recurse if the operands are not constant
            if not(isinstance(node.left, ast.Constant)): node.left = simplify_internal(node.left)
            if not(isinstance(node.right, ast.Constant)): node.right = simplify_internal(node.right)
            # simplify addition of constants or addition with 0
            if isinstance(node.op, ast.Add):
                if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant): return ast.Constant(node.left.value + node.right.value)
                elif isinstance(node.left, ast.Constant) and node.left.value == 0: return node.right
                elif isinstance(node.right, ast.Constant) and node.right.value == 0: return node.left
            # simplify subtractions of constants or subtraction with 0
            elif isinstance(node.op, ast.Sub):
                if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant): return ast.Constant(node.left.value - node.right.value)
                elif isinstance(node.left, ast.Constant) and node.left.value == 0: return ast.UnaryOp(ast.USub(), node.right)
                elif isinstance(node.right, ast.Constant) and node.right.value == 0: return node.left
            # simplify multiplication of constants or multiplication by 0 or 1 or -1
            if isinstance(node.op, ast.Mult):
                if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant): return ast.Constant(node.left.value * node.right.value)
                elif isinstance(node.left, ast.Constant) and node.left.value == 0: return ast.Constant(0)
                elif isinstance(node.right, ast.Constant) and node.right.value == 0: return ast.Constant(0)
                elif isinstance(node.left, ast.Constant) and node.left.value == 1: return node.right
                elif isinstance(node.right, ast.Constant) and node.right.value == 1: return node.left
                elif isinstance(node.left, ast.Constant) and node.left.value == -1: return ast.UnaryOp(ast.USub(), node.right)
                elif isinstance(node.right, ast.Constant) and node.right.value == -1: return ast.UnaryOp(ast.USub(), node.left)
            # simplify division of constants or division of the form 0/x, x/1, x/-1
            if isinstance(node.op, ast.Div):
                if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant): return ast.Constant(node.left.value / node.right.value)
                elif isinstance(node.left, ast.Constant) and node.left.value == 0: return ast.Constant(0)
                elif isinstance(node.right, ast.Constant) and node.right.value == 1: return node.left
                elif isinstance(node.right, ast.Constant) and node.right.value == -1: return ast.UnaryOp(ast.USub(), node.left)
            # simplify integer division of constants or integer division of the form 0/x, x/1, x/-1
            if isinstance(node.op, ast.FloorDiv):
                if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant): return ast.Constant(node.left.value // node.right.value)
                elif isinstance(node.left, ast.Constant) and node.left.value == 0: return ast.Constant(0)
                elif isinstance(node.right, ast.Constant) and node.right.value == 1: return node.left
                elif isinstance(node.right, ast.Constant) and node.right.value == -1: return ast.UnaryOp(ast.USub(), node.left)
            # simplify mod of constants or mod of the form 0 % x, x % 1
            if isinstance(node.op, ast.Mod):
                if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant): return ast.Constant(node.left.value % node.right.value)
                elif isinstance(node.left, ast.Constant) and node.left.value == 0: return ast.Constant(0)
                elif isinstance(node.right, ast.Constant) and node.right.value == 1: return ast.Constant(0)
            # simplify exponentiation of constants or exponentiations of the form x ** 0, x ** 1, 1 ** x
            if isinstance(node.op, ast.Pow):
                if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant): return ast.Constant(node.left.value ** node.right.value)
                elif isinstance(node.right, ast.Constant) and node.right.value == 0: return ast.Constant(1)
                elif isinstance(node.right, ast.Constant) and node.right.value == 1: return node.left
                elif isinstance(node.left, ast.Constant) and node.left.value == 1: return ast.Constant(1)
            # simplify shifts of constants or shifts of the form x << 0, 0 << y
            if isinstance(node.op, ast.LShift):
                if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant): return ast.Constant(node.left.value << node.right.value)
                elif isinstance(node.right, ast.Constant) and node.right.value == 0: return node.left
                elif isinstance(node.left, ast.Constant) and node.left.value == 0: return ast.Constant(0)
            # simplify shifts of constants or shifts of the form x >> 0, 0 >> y
            if isinstance(node.op, ast.RShift):
                if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant): return ast.Constant(node.left.value >> node.right.value)
                elif isinstance(node.right, ast.Constant) and node.right.value == 0: return node.left
                elif isinstance(node.left, ast.Constant) and node.left.value == 0: return ast.Constant(0)
            # simplify bitwise OR of constants or ORs of the form x | 0, 0 | x
            if isinstance(node.op, ast.BitOr):
                if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant): return ast.Constant(node.left.value | node.right.value)
                elif isinstance(node.right, ast.Constant) and node.right.value == 0: return node.left
                elif isinstance(node.left, ast.Constant) and node.left.value == 0: return node.right
            # simplify bitwise XOR of constants or XORs of the form x ^ 0, 0 ^ x
            if isinstance(node.op, ast.BitXor):
                if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant): return ast.Constant(node.left.value ^ node.right.value)
                elif isinstance(node.right, ast.Constant) and node.right.value == 0: return node.left
                elif isinstance(node.left, ast.Constant) and node.left.value == 0: return node.right
            # simplify bitwise AND of constants or ANDs of the form x & 0, 0 & x
            if isinstance(node.op, ast.BitAnd):
                if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant): return ast.Constant(node.left.value & node.right.value)
                elif isinstance(node.right, ast.Constant) and node.right.value == 0: return ast.Constant(0)
                elif isinstance(node.left, ast.Constant) and node.left.value == 0: return ast.Constant(0)
            return node
    o = BinOpSimplifier().visit(o)
    ast.fix_missing_locations(o)
    return o
