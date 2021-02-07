import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization

def f_constant(x, y):
    a = 7
    return 3
def f_constant_expected_result(x, y):
    a = 7
    return 3
def f_variable(x, y):
    a = 7
    return a
def f_variable_expected_result(x, y):
    a = 7
    return a
def f_attribute(x, y):
    return x.a
def f_attribute_expected_result(x, y):
    ret0 = x.a
    return ret0
def f_operator(x, y):
    a = 7
    return y + b
def f_operator_expected_result(x, y):
    a = 7
    ret0 = y + b
    return ret0
def f_multiple_return(x, y):
    if x:
        return y + 1
    else:
        return y + 2
def f_multiple_return_expected_result(x, y):
    if x:
        ret0 = y + 1
        return ret0
    else:
        ret1 = y + 2
        return ret1


def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestCanonicalizeReturn(unittest.TestCase):
    def test_constant(self):
        f = gamehop.inlining.internal.get_function_def(f_constant)
        gamehop.verification.canonicalization.canonicalize_return(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_constant_expected_result)
        )
    def test_variable(self):
        f = gamehop.inlining.internal.get_function_def(f_variable)
        gamehop.verification.canonicalization.canonicalize_return(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_variable_expected_result)
        )
    def test_attribute(self):
        f = gamehop.inlining.internal.get_function_def(f_attribute)
        gamehop.verification.canonicalization.canonicalize_return(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_attribute_expected_result)
        )
    def test_operator(self):
        f = gamehop.inlining.internal.get_function_def(f_operator)
        gamehop.verification.canonicalization.canonicalize_return(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_operator_expected_result)
        )
    def test_multiple_return(self):
        f = gamehop.inlining.internal.get_function_def(f_multiple_return)
        gamehop.verification.canonicalization.canonicalize_return(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_multiple_return_expected_result)
        )
