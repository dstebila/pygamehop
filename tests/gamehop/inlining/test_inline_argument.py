import ast
import inspect
import unittest

import gamehop.inlining

def bool_f(x, y):
    print(x)
def bool_f_expected_result(y):
    print(True)
def float_f(x):
    print(x)
def float_f_expected_result():
    print(3.14152)
def int_f(x):
    print(x)
def int_f_expected_result():
    print(42)
def str_f(x):
    print(x)
def str_f_expected_result():
    print("potato")
def tuple_f(x, y):
    print(x)
def tuple_f_expected_result(y):
    print((1, 2, 3))
def assigned_f(x):
    print(x)
    x = 123

def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestInlineArgument(unittest.TestCase):
    def test_bool(self):
        self.assertEqual(
            gamehop.inlining.inline_argument(bool_f, 'x', True),
            expected_result(bool_f_expected_result))
    def test_float(self):
        self.assertEqual(
            gamehop.inlining.inline_argument(float_f, 'x', 3.14152),
            expected_result(float_f_expected_result))
    def test_int(self):
        self.assertEqual(
            gamehop.inlining.inline_argument(int_f, 'x', 42),
            expected_result(int_f_expected_result))
    def test_str(self):
        self.assertEqual(
            gamehop.inlining.inline_argument(str_f, 'x', 'potato'),
            expected_result(str_f_expected_result))
    def test_tuple(self):
        self.assertEqual(
            gamehop.inlining.inline_argument(tuple_f, 'x', (1, 2, 3)),
            expected_result(tuple_f_expected_result))
    def test_tuple_ast(self):
        tupleast = ast.Tuple([ast.Constant(1), ast.Constant(2), ast.Constant(3)], ctx=ast.Load())
        self.assertEqual(
            gamehop.inlining.inline_argument(tuple_f, 'x', tupleast),
            expected_result(tuple_f_expected_result))
    def test_f_as_string(self):
        str_bool_f = "def bool_f(x, y): print(x)"
        self.assertEqual(
            gamehop.inlining.inline_argument(str_bool_f, 'x', True),
            expected_result(bool_f_expected_result))
    def test_assigned(self):
        with self.assertRaisesRegex(NotImplementedError, "Cannot handle cases where the inlined variable is assigned to"):
            gamehop.inlining.inline_argument(assigned_f, 'x', True)
