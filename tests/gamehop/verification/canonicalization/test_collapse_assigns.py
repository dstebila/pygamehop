import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization

def f_constant(y):
    a = 7
    x = a
    return x
def f_constant_expected_result(y):
    return 7
def f_variable(y):
    a = y
    x = a
    return x
def f_variable_expected_result(y):
    return y
def f_reassign(y):
    a = y
    x = a
    g(x)
    a = 7
    x = a
    g(x)
def f_reassign_expected_result(y):
    g(y)
    g(7)


def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestCollapseAssigns(unittest.TestCase):
    def test_constant(self):
        f = gamehop.inlining.internal.get_function_def(f_constant)
        gamehop.verification.canonicalization.collapse_useless_assigns(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_constant_expected_result)
        )
    def test_variable(self):
        f = gamehop.inlining.internal.get_function_def(f_variable)
        gamehop.verification.canonicalization.collapse_useless_assigns(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_variable_expected_result)
        )
    def test_reassign(self):
        f = gamehop.inlining.internal.get_function_def(f_reassign)
        gamehop.verification.canonicalization.collapse_useless_assigns(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_reassign_expected_result)
        )
