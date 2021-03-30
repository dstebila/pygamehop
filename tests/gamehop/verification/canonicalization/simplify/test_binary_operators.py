import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization.simplify as simplify

def f_add(y):
    a = 3 + 4
    b = 0 + y
def f_add_expected_result(y):
    a = 7
    b = y
def f_sub(y):
    a = 3 - 4
    b = 0 - y
    c = y - 0
def f_sub_expected_result(y):
    a = -1
    b = -y
    c = y
def f_mult(y):
    a = 3 * 4
    b = 0 * y
    c = 1 * y
    d = y * -1
def f_mult_expected_result(y):
    a = 12
    b = 0
    c = y
    d = -y
def f_div(y):
    a = 6/2
    b = 0 / y
    c = y / 1
    d = y / -1
def f_div_expected_result(y):
    a = 3.0
    b = 0
    c = y
    d = -y

def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestSimplifyBinaryOperators(unittest.TestCase):
    def test_add(self):
        f = gamehop.inlining.internal.get_function_def(f_add)
        f = simplify.binary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_add_expected_result)
        )
    def test_sub(self):
        f = gamehop.inlining.internal.get_function_def(f_sub)
        f = simplify.binary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_sub_expected_result)
        )
    def test_mult(self):
        f = gamehop.inlining.internal.get_function_def(f_mult)
        f = simplify.binary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_mult_expected_result)
        )
    def test_div(self):
        f = gamehop.inlining.internal.get_function_def(f_div)
        f = simplify.binary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_div_expected_result)
        )
