import ast
import inspect
import unittest

import gamehop.utils
import gamehop.verification.canonicalization.expand

def expected_result(f):
    fdef = gamehop.utils.get_function_def(f)
    fdef.name = fdef.name.replace('_expected_result', '')
    return ast.unparse(fdef)

def do_it(tester, f, f_expected_result):
    fdef = gamehop.utils.get_function_def(f)
    gamehop.verification.canonicalization.expand.ifexpressions(fdef)
    tester.assertEqual(ast.unparse(fdef), expected_result(f_expected_result))

class TestExpandIfExpr(unittest.TestCase):

    def test_basic(self):
        def f_basic(): a = b if c else d
        def f_basic_expected_result(): a = b if c else d
        do_it(self, f_basic, f_basic_expected_result)

    def test_many(self):
        def f_many(y):
            a = b(y) if c(y) else d(y)
            e = f(y) if g(y) else h
        def f_many_expected_result(y):
            φ0 = b(y)
            φ1 = c(y)
            φ2 = d(y)
            a = φ0 if φ1 else φ2
            φ3 = f(y)
            φ4 = g(y)
            e = φ3 if φ4 else h
        do_it(self, f_many, f_many_expected_result)

    def test_recursive(self):
        def f_recursive(y):
            a = b(y) if c(y) else d(y) if e(y) else f(y)
        def f_recursive_expected_result(y):
            φ0 = b(y)
            φ1 = c(y)
            φ2 = d(y) if e(y) else f(y)
            a = φ0 if φ1 else φ2
        do_it(self, f_recursive, f_recursive_expected_result)
