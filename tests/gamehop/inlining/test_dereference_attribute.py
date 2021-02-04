import ast
import inspect
import unittest

import gamehop.inlining.internal

def f_basic(x):
    y = x.z
    x.y = z
def f_basic_expected_result(x):
    y = x_z
    x_y = z
def f_nested(x):
    y = x.z.w
def f_nested_expected_result(x):
    y = x_z.w
def f_not_actually_nested(x):
    y = z.x.w
def f_not_actually_nested_2(x):
    y = z.x.x.w

def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestDereferenceAttribute(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(
            gamehop.inlining.internal.dereference_attribute(f_basic, 'x', 'x_{:s}'),
            expected_result(f_basic_expected_result))
    def test_nested(self):
        self.assertEqual(
            gamehop.inlining.internal.dereference_attribute(f_nested, 'x', 'x_{:s}'),
            expected_result(f_nested_expected_result))
    def test_not_actually_nested(self):
        self.assertEqual(
            gamehop.inlining.internal.dereference_attribute(f_not_actually_nested, 'x', 'x_{:s}'),
            expected_result(f_not_actually_nested))
    def test_not_actually_nested_2(self):
        self.assertEqual(
            gamehop.inlining.internal.dereference_attribute(f_not_actually_nested_2, 'x', 'x_{:s}'),
            expected_result(f_not_actually_nested_2))
