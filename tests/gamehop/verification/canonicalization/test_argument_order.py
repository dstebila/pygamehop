import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization as canonicalization
import gamehop.utils as utils


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
def f_arith(y: int, x: int):
    r = x + 2 * y
    return r
def f_arith_expected_result(x: int, y: int):
    r = x + 2 * y
    return r

def expected_result(f):
    fdef = gamehop.utils.get_function_def(f)
    fdef.name = fdef.name.replace('_expected_result', '')
    return ast.unparse(fdef)

class TestCanonicalizeArgumentOrder(unittest.TestCase):
    def test_basic1(self):
        f = gamehop.utils.get_function_def(f_basic1)
        gamehop.verification.canonicalization.canonicalize_argument_order(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_basic1_expected_result)
        )
    def test_basic2(self):
        f = gamehop.utils.get_function_def(f_basic2)
        gamehop.verification.canonicalization.canonicalize_argument_order(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_basic2_expected_result)
        )
    def test_unused_arg(self):
        f = gamehop.utils.get_function_def(f_unused_arg)
        gamehop.verification.canonicalization.canonicalize_argument_order(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_unused_arg_expected_result)
        )
    def test_arith(self):
        f = gamehop.utils.get_function_def(f_arith)
        gamehop.verification.canonicalization.canonicalize_argument_order(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_arith_expected_result)
        )

    def test_two_uses(self):
        def g(x): pass
        def f(a,b):
            g(a)
            g(b)
            g(a)

        def f_expected_result(a,b):
            g(a)
            g(b)
            g(a)

        fdef = utils.get_function_def(f)
        canonicalization.canonicalize_argument_order(fdef)
        self.assertEqual(
            ast.unparse(fdef),
            expected_result(f_expected_result)
        )

    def test_assign_overwrites(self):
        def f(a,b):
            a = 3
            return a

        def f_expected_result():
            a = 3
            return a

        fdef = utils.get_function_def(f)
        canonicalization.canonicalize_argument_order(fdef)
        self.assertEqual(
            ast.unparse(fdef),
            expected_result(f_expected_result)
        )

    def test_inner_function_argument_overwrites(self):
        def f(a,b):
            def g(a,c):
                return a

        def f_expected_result():
            def g(a):
                return a

        fdef = utils.get_function_def(f)
        canonicalization.canonicalize_argument_order(fdef)
        self.assertEqual(
            ast.unparse(fdef),
            expected_result(f_expected_result)
        )

    def test_inner_function_assign_overwrites(self):
        def f(a,b):
            def g(c):
                a = 3
                return a

        def f_expected_result():
            def g():
                a = 3
                return a

        fdef = utils.get_function_def(f)
        canonicalization.canonicalize_argument_order(fdef)
        self.assertEqual(
            ast.unparse(fdef),
            expected_result(f_expected_result)
        )
