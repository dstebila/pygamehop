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
    gamehop.verification.canonicalization.expand.expand_non_compact_expressions(fdef)
    tester.assertEqual(ast.unparse(fdef), expected_result(f_expected_result))

class TestExpand(unittest.TestCase):

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
            φ0 = c(y)
            φ1 = b(y)
            φ2 = d(y)
            a = φ1 if φ0 else φ2
            φ3 = g(y)
            φ4 = f(y)
            e = φ4 if φ3 else h
        do_it(self, f, f_expected_result)

    def test_recursive(self):
        def f(y):
            a = b(y) if c(y) else d(y) if e(y) else f(y)
        def f_expected_result(y):
            φ0 = c(y)
            φ1 = b(y)
            φ2 = e(y)
            φ3 = d(y)
            φ4 = f(y)
            φ5 = φ3 if φ2 else φ4
            a = φ1 if φ0 else φ5
        do_it(self, f, f_expected_result)
