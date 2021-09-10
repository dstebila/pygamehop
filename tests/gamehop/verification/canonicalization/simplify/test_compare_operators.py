import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization.simplify as simplify

def f_compareF(y):
    a = 1 == 2 == 3
    b = 1 != 1
    c = 1 < 0
    d = 1 <= 0
    e = 1 > 2
    f = 1 >= 2
    g = 's' in 'potato'
    h = 's' not in 'test'
    i = 1 < 2 < 4 < 8 < 0
def f_compareF_expected_result(y):
    a = False
    b = False
    c = False
    d = False
    e = False
    f = False
    g = False
    h = False
    i = False
def f_compareT(y):
    a = 1 == 1
    b = 1 != 2
    c = 1 < 2
    d = 1 <= 2 < 3
    e = 1 > 0
    f = 1 >= 0
    g = 's' in 'test'
    h = 's' not in 'potato'
    i = 1 < 2 < 4 < 8 < 16
def f_compareT_expected_result(y):
    a = True
    b = True
    c = True
    d = True
    e = True
    f = True
    g = True
    h = True
    i = True


def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestSimplifyCompareOperators(unittest.TestCase):
    def test_compareF(self):
        f = gamehop.utils.get_function_def(f_compareF)
        f = simplify.simplify(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_compareF_expected_result)
        )
    def test_compareT(self):
        f = gamehop.utils.get_function_def(f_compareT)
        f = simplify.simplify(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_compareT_expected_result)
        )
