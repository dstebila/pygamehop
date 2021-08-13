import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization.expand as expand

def f_noop(y):
    a = f(y)
def f_noop_expected_result(y):
    a = f(y)
def f_basic(y):
    a = f(g(y))
def f_basic_expected_result(y):
    φ0 = g(y)
    a = f(φ0)
def f_many(y):
    a = f(g(y), h(i(z, j(w))))
    b = f(a, k(y))
def f_many_expected_result(y):
    φ0 = g(y)
    φ1 = j(w)
    φ2 = i(z, φ1)
    φ3 = h(φ2)
    a = f(φ0, φ3)
    φ4 = k(y)
    b = f(a, φ4)
def f_barecall(y):
    f(g(y))
def f_barecall_expected_result(y):
    φ0 = g(y)
    f(φ0)

def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestExpandCallArguments(unittest.TestCase):
    def test_noop(self):
        f = gamehop.utils.get_function_def(f_noop)
        expand.call_arguments(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_noop_expected_result)
        )
    def test_basic(self):
        f = gamehop.utils.get_function_def(f_basic)
        expand.call_arguments(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_basic_expected_result)
        )
    def test_many(self):
        f = gamehop.utils.get_function_def(f_many)
        expand.call_arguments(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_many_expected_result)
        )
    def test_barecall(self):
        f = gamehop.utils.get_function_def(f_barecall)
        expand.call_arguments(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_barecall_expected_result)
        )
