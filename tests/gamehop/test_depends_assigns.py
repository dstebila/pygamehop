import ast
import inspect
import unittest

import gamehop.utils
    # if isinstance(node, ast.Assign): return vars_depends_on(node.value)
    # elif isinstance(node, ast.Attribute): return vars_depends_on(node.value)
    # elif isinstance(node, ast.BinOp): return vars_depends_on(node.left) + vars_depends_on(node.right)
    # elif isinstance(node, ast.Call): return vars_depends_on(node.func) + sum([vars_depends_on(arg) for arg in node.args], start=[])
    # elif isinstance(node, ast.Constant): return []
    # elif isinstance(node, ast.Name): return [node.id] if isinstance(node.ctx, ast.Load) else []
    # elif isinstance(node, ast.Return): return [] if node.value == None else vars_depends_on(node.value)
    # elif isinstance(node, ast.Tuple): return sum([vars_depends_on(e) for e in node.elts], start=[])

class TestDependsOn(unittest.TestCase):

    def test_Assign(self):
        s = 'a = b'
        self.assertEqual(gamehop.utils.vars_depends_on(ast.parse(s).body[0]), ['b'])

    def test_Attribute(self):
        s = 'a = x.y(z)'
        self.assertEqual(gamehop.utils.vars_depends_on(ast.parse(s).body[0]), ['x', 'z'])

    def test_BinOp(self):
        s = 'a = x + y'
        self.assertEqual(gamehop.utils.vars_depends_on(ast.parse(s).body[0]), ['x', 'y'])

    def test_Call(self):
        s = 'a = x(y, z)'
        self.assertEqual(gamehop.utils.vars_depends_on(ast.parse(s).body[0]), ['x', 'y', 'z'])

    def test_CallAttribute(self):
        s = 'a = b.x(y, z)'
        self.assertEqual(gamehop.utils.vars_depends_on(ast.parse(s).body[0]), ['b', 'y', 'z'])

    def test_Constant(self):
        s = 'a = 7'
        self.assertEqual(gamehop.utils.vars_depends_on(ast.parse(s).body[0]), [])

    def test_Name(self):
        s = 'a = b'
        self.assertEqual(gamehop.utils.vars_depends_on(ast.parse(s).body[0]), ['b'])

    def test_Return(self):
        s = 'return b'
        self.assertEqual(gamehop.utils.vars_depends_on(ast.parse(s).body[0]), ['b'])

    def test_Tuple(self):
        s = 'a = (b, c)'
        self.assertEqual(gamehop.utils.vars_depends_on(ast.parse(s).body[0]), ['b', 'c'])

class TestAssignsTo(unittest.TestCase):

    def test_Assign(self):
        s = 'a = b'
        self.assertEqual(gamehop.utils.vars_assigns_to(ast.parse(s).body[0]), ['a'])

    def test_Attribute(self):
        s = 'a = x.y(z)'
        self.assertEqual(gamehop.utils.vars_assigns_to(ast.parse(s).body[0]), ['a'])

    def test_BinOp(self):
        s = 'a = x + y'
        self.assertEqual(gamehop.utils.vars_assigns_to(ast.parse(s).body[0]), ['a'])

    def test_Call(self):
        s = 'a = x(y, z)'
        self.assertEqual(gamehop.utils.vars_assigns_to(ast.parse(s).body[0]), ['a'])

    def test_CallAttribute(self):
        s = 'a = b.x(y, z)'
        self.assertEqual(gamehop.utils.vars_assigns_to(ast.parse(s).body[0]), ['a'])

    def test_Constant(self):
        s = 'a = 7'
        self.assertEqual(gamehop.utils.vars_assigns_to(ast.parse(s).body[0]), ['a'])

    def test_Name(self):
        s = 'a = b'
        self.assertEqual(gamehop.utils.vars_assigns_to(ast.parse(s).body[0]), ['a'])

    def test_Return(self):
        s = 'return b'
        self.assertEqual(gamehop.utils.vars_assigns_to(ast.parse(s).body[0]), [])

    def test_Tuple(self):
        s = 'a = (b, c)'
        self.assertEqual(gamehop.utils.vars_assigns_to(ast.parse(s).body[0]), ['a'])

    def test_Tuple2(self):
        s = '(a1, a2) = (b, c)'
        self.assertEqual(gamehop.utils.vars_assigns_to(ast.parse(s).body[0]), ['a1', 'a2'])

    def test_cryptoexample1(self):
        s = '(v2, v3) = v1.KeyGen()'
        self.assertEqual(gamehop.utils.vars_depends_on(ast.parse(s).body[0]), ['v1'])
        self.assertEqual(gamehop.utils.vars_assigns_to(ast.parse(s).body[0]), ['v2', 'v3'])
        s = 'v4 = v1.Encrypt(v2, v5)'
        self.assertEqual(gamehop.utils.vars_depends_on(ast.parse(s).body[0]), ['v1', 'v2', 'v5'])
        self.assertEqual(gamehop.utils.vars_assigns_to(ast.parse(s).body[0]), ['v4'])
        s = 'v5 = Crypto.UniformlySample(SharedSecret)'
        self.assertEqual(gamehop.utils.vars_depends_on(ast.parse(s).body[0]), ['Crypto', 'SharedSecret'])
        self.assertEqual(gamehop.utils.vars_assigns_to(ast.parse(s).body[0]), ['v5'])
        s = 'v6 = v0.guess(v2, v4, v5)'
        self.assertEqual(gamehop.utils.vars_depends_on(ast.parse(s).body[0]), ['v0', 'v2', 'v4', 'v5'])
        self.assertEqual(gamehop.utils.vars_assigns_to(ast.parse(s).body[0]), ['v6'])
        s = 'return v6'
        self.assertEqual(gamehop.utils.vars_depends_on(ast.parse(s).body[0]), ['v6'])
        self.assertEqual(gamehop.utils.vars_assigns_to(ast.parse(s).body[0]), [])
