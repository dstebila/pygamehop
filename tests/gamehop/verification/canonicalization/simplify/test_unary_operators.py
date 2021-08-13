import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization.simplify as simplify

def f_uadd(y):
    a = +3
def f_uadd_expected_result(y):
    a = 3
def f_nested_usub(y):
    a = -(-(3))
def f_nested_usub_expected_result(y):
    a = 3
def f_not(y):
    a = not(False)
def f_not_expected_result(y):
    a = True
def f_nested_not(y):
    a = not(not(False))
def f_nested_not_expected_result(y):
    a = False


def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestSimplifyUnaryOperators(unittest.TestCase):
    def test_uadd(self):
        f = gamehop.utils.get_function_def(f_uadd)
        f = simplify.unary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_uadd_expected_result)
        )
    def test_nested_usub(self):
        f = gamehop.utils.get_function_def(f_nested_usub)
        f = simplify.unary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_nested_usub_expected_result)
        )
    def test_not(self):
        f = gamehop.utils.get_function_def(f_not)
        f = simplify.unary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_not_expected_result)
        )
    def test_nested_not(self):
        f = gamehop.utils.get_function_def(f_nested_not)
        f = simplify.unary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_nested_not_expected_result)
        )
