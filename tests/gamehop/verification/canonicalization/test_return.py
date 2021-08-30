import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization

def expected_result(f):
    fdef = gamehop.utils.get_function_def(f)
    fdef.name = fdef.name.replace('_expected_result', '')
    return ast.unparse(fdef)

class TestCanonicalizeReturn(unittest.TestCase):
    def test_constant(self):
        def f_constant(x, y):
            a = 7
            return 3
        def f_constant_expected_result(x, y):
            a = 7
            return 3
        f = gamehop.utils.get_function_def(f_constant)
        gamehop.verification.canonicalization.canonicalize_return(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_constant_expected_result)
        )
    def test_variable(self):
        def f_variable(x, y):
            a = 7
            return a
        def f_variable_expected_result(x, y):
            a = 7
            return a
        f = gamehop.utils.get_function_def(f_variable)
        gamehop.verification.canonicalization.canonicalize_return(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_variable_expected_result)
        )
    def test_tuple(self):
        def f_tuple(x, y):
            a = 7
            return (a, x, y)
        def f_tuple_expected_result(x, y):
            a = 7
            ρ = (a, x, y)
            return ρ
        f = gamehop.utils.get_function_def(f_tuple)
        gamehop.verification.canonicalization.canonicalize_return(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_tuple_expected_result)
        )
    def test_attribute(self):
        def f_attribute(x, y):
            return x.a
        def f_attribute_expected_result(x, y):
            ρ = x.a
            return ρ
        f = gamehop.utils.get_function_def(f_attribute)
        gamehop.verification.canonicalization.canonicalize_return(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_attribute_expected_result)
        )
    def test_operator(self):
        def f_operator(x, y):
            a = 7
            return y + a
        def f_operator_expected_result(x, y):
            a = 7
            ρ = y + a
            return ρ
        f = gamehop.utils.get_function_def(f_operator)
        gamehop.verification.canonicalization.canonicalize_return(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_operator_expected_result)
        )
