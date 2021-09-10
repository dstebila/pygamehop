import ast
import copy
from .. import utils

class NodeSimplifier(utils.NewNodeTransformer):
    def visit_UnaryOp(self, node):
        node = self.generic_visit(node)
        if not(isinstance(node.operand, ast.Constant)): return node

        # do replacements based on operator type
        if isinstance(node.op, ast.UAdd): return node.operand
        elif isinstance(node.op, ast.USub): return ast.Constant(-node.operand.value)
        elif isinstance(node.op, ast.Not): return ast.Constant(not(node.operand.value))
        elif isinstance(node.op, ast.Invert): return ast.Constant(~node.operand.value)
        assert False

    def visit_BoolOp(self, node):
        node = self.generic_visit(node)

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

    def visit_BinOp(self, node):
        node = self.generic_visit(node)
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

    def visit_Compare(self, node):
        node = self.generic_visit(node)
        # can't do anything if they're not constants by now
        if not(isinstance(node.left, ast.Constant)): return node
        for i in range(len(node.comparators)):
            if not(isinstance(node.comparators[i], ast.Constant)): return node
        # compute the actual value
        truthValue = True
        values = []
        values.append(node.left.value)
        for c in node.comparators:
            values.append(c.value)
        for i, op in enumerate(node.ops):
            a = values[i]
            b = values[i+1]
            if isinstance(op, ast.Eq): truthValue = truthValue and (a == b)
            elif isinstance(op, ast.NotEq): truthValue = truthValue and (a != b)
            elif isinstance(op, ast.Lt): truthValue = truthValue and (a < b)
            elif isinstance(op, ast.LtE): truthValue = truthValue and (a <= b)
            elif isinstance(op, ast.Gt): truthValue = truthValue and (a > b)
            elif isinstance(op, ast.GtE): truthValue = truthValue and (a >= b)
            elif isinstance(op, ast.Is): truthValue = truthValue and (a is b)
            elif isinstance(op, ast.IsNot): truthValue = truthValue and (a is not  b)
            elif isinstance(op, ast.In): truthValue = truthValue and (a in b)
            elif isinstance(op, ast.NotIn): truthValue = truthValue and (a not in b)
            else: raise ValueError("Unsupported comparator: {:s}".format(str(type(op))))
        return ast.Constant(truthValue)

    def visit_IfExp(self, node):
        node = self.generic_visit(node)
        if not(isinstance(node.test, ast.Constant)): return node
        return node.body if node.test.value else node.orelse



def simplify(f: ast.stmt) -> ast.stmt:
    """Modify (in place) the given function definition so that all expressions
    involving constants are simplified."""
    # go through each statement in the body
    # newbody = list()
    # for stmt in f.body:
    #     newbody.append(simplify_internal(stmt))
    # f.body = newbody
    f = NodeSimplifier().visit(f)
    ast.fix_missing_locations(f)
    return f
