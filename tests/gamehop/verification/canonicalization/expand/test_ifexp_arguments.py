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

class TestExpandIfExp(unittest.TestCase):

    def test_basic(self):
        def f(): a = b if c else d
        def f_expected_result(): a = b if c else d
        do_it(self, f, f_expected_result)

    def test_basic(self):
        def f(): a = b if c else d
        def f_expected_result(): a = b if c else d
        do_it(self, f, f_expected_result)

    def test_many(self):
        def f(y):
            a = b(y) if c(y) else d(y)
            e = f(y) if g(y) else h
        def f_expected_result(y):
            φifexp0 = b(y)
            φifexp1 = c(y)
            φifexp2 = d(y)
            a = φifexp0 if φifexp1 else φifexp2
            φifexp3 = f(y)
            φifexp4 = g(y)
            e = φifexp3 if φifexp4 else h
        do_it(self, f, f_expected_result)

    def test_recursive(self):
        def f(y):
            a = b(y) if c(y) else d(y) if e(y) else f(y)
        def f_expected_result(y):
            φifexp0 = b(y)
            φifexp1 = c(y)
            φifexp2 = d(y)
            φifexp3 = e(y)
            φifexp4 = f(y)
            φifexp5 = φifexp2 if φifexp3 else φifexp4
            a = φifexp0 if φifexp1 else φifexp5
        do_it(self, f, f_expected_result)

TestExpandIfExp().test_many()
