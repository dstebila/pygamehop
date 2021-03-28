import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization

def f_basic1(x, y):
    v = 3
    (u, w) = (1, 2)
    r = (u, v)
    return r
def f_basic1_expected_result(x, y):
    (u, w) = (1, 2)
    v = 3
    r = (u, v)
    return r
def f_basic2(x, y):
    (u, v) = (1, 2)
    v = 3
    r = (u, v)
    return r
def f_basic2_expected_result(x, y):
    (u, v) = (1, 2)
    v = 3
    r = (u, v)
    return r
def f_basic3(x, y):
    u = 1
    w = 3
    v = 2
    r = (u, v, w)
    return r
def f_basic3_expected_result(x, y):
    u = 1
    v = 2
    w = 3
    r = (u, v, w)
    return r
def f_ordering(a):
    c = h(a)
    d = g(c)
    b = g(c)
    r = (b, c, d)
    return r
def f_ordering_expected_result(a):
    c = h(a)
    b = g(c)
    d = g(c)
    r = (b, c, d)
    return r
def f_KEMfromPKEtestcase1(pke):
    m0 = h(pke.MS)
    m1 = h(pke.MS)    
    ct = E(m0)
    r = g(ct, m1)
    return r
def f_KEMfromPKEtestcase2(pke):
    m0 = h(pke.MS)
    ct = E(m0)
    m1 = h(pke.MS)
    r = g(ct, m1)
    return r


def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestCanonicalizeLineOrder(unittest.TestCase):
    def test_basic1(self):
        f = gamehop.inlining.internal.get_function_def(f_basic1)
        gamehop.verification.canonicalization.canonicalize_line_order(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_basic1_expected_result)
        )
    def test_basic2(self):
        f = gamehop.inlining.internal.get_function_def(f_basic2)
        gamehop.verification.canonicalization.canonicalize_line_order(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_basic2_expected_result)
        )
    def test_basic3(self):
        f = gamehop.inlining.internal.get_function_def(f_basic3)
        gamehop.verification.canonicalization.canonicalize_line_order(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_basic3_expected_result)
        )
    def test_ordering(self):
        f = gamehop.inlining.internal.get_function_def(f_ordering)
        gamehop.verification.canonicalization.canonicalize_line_order(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_ordering_expected_result)
        )
    def test_KEMfromPKEtestcase(self):
        f1 = gamehop.inlining.internal.get_function_def(f_KEMfromPKEtestcase1)
        f2 = gamehop.inlining.internal.get_function_def(f_KEMfromPKEtestcase2)
        gamehop.verification.canonicalization.canonicalize_line_order(f1)
        gamehop.verification.canonicalization.canonicalize_line_order(f2)
        s1 = ast.unparse(f1).replace('f_KEMfromPKEtestcase1', 'f')
        s2 = ast.unparse(f2).replace('f_KEMfromPKEtestcase2', 'f')
        self.assertEqual(s1, s2)