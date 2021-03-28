import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization

def f_basic1(x, y):
    r = (x, y)
    return r
def f_basic1_expected_result(x, y):
    r = (x, y)
    return r
def f_basic2(x, y):
    r = (y, x)
    return r
def f_basic2_expected_result(y, x):
    r = (y, x)
    return r
def f_unused_arg(x, y):
    r = (7, y)
    return r
def f_unused_arg_expected_result(y):
    r = (7, y)
    return r
def f_arith(x: int, y: int):
    r = x + 2 * y
    return r
def f_arith_expected_result(y: int, x: int):
    r = x + 2 * y
    return r

def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestCanonicalizeArgumentOrder(unittest.TestCase):
    def test_basic1(self):
        f = gamehop.inlining.internal.get_function_def(f_basic1)
        gamehop.verification.canonicalization.canonicalize_argument_order(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_basic1_expected_result)
        )
    def test_basic2(self):
        f = gamehop.inlining.internal.get_function_def(f_basic2)
        gamehop.verification.canonicalization.canonicalize_argument_order(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_basic2_expected_result)
        )
    def test_unused_arg(self):
        f = gamehop.inlining.internal.get_function_def(f_unused_arg)
        gamehop.verification.canonicalization.canonicalize_argument_order(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_unused_arg_expected_result)
        )
    def arith(self):
        s1 = gamehop.verification.canonicalize_function(f_arith)
        s2 = gamehop.verification.canonicalize_function(expected_result(f_arith_expected_result))
        self.assertEqual(s1, s2)
