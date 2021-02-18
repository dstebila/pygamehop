import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization.expand as expand

def f_noop(y):
    a = f(y)
    g = f(a)
    return g
def f_noop_expected_result(y):
    a = f(y)
    g = f(a)
    return g
def f_basic(y):
    a = f(y)
    a = f(a)
    a = f(a)
    g = f(a)
    g = f(g)
    return g
def f_basic_expected_result(y):
    a = f(y)
    aν1 = f(a)
    aν2 = f(aν1)
    g = f(aν2)
    gν1 = f(g)
    return gν1
def f_multitarget(y):
    b = a = f(y)
    b = a = f(a)
    g = f(a)
    return g
def f_multitarget_expected_result(y):
    b = a = f(y)
    bν1 = aν1 = f(a)
    g = f(aν1)
    return g
def f_tuple(y):
    (a, b) = f(y)
    (a, b) = f(a)
    g = f(a)
def f_tuple_expected_result(y):
    (a, b) = f(y)
    (aν1, bν1) = f(a)
    g = f(aν1)
def f_if(y):
    if f(x) == f(y): pass

def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestExpandVariableReassign(unittest.TestCase):
    def test_noop(self):
        f = gamehop.inlining.internal.get_function_def(f_noop)
        expand.variable_reassign(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_noop_expected_result)
        )
    def test_basic(self):
        f = gamehop.inlining.internal.get_function_def(f_basic)
        expand.variable_reassign(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_basic_expected_result)
        )
    def test_multit(self):
        f = gamehop.inlining.internal.get_function_def(f_multitarget)
        expand.variable_reassign(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_multitarget_expected_result)
        )
    def test_tuple(self):
        f = gamehop.inlining.internal.get_function_def(f_tuple)
        expand.variable_reassign(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_tuple_expected_result)
        )
    def test_if(self):
        f = gamehop.inlining.internal.get_function_def(f_if)
        with self.assertRaises(NotImplementedError):
            expand.variable_reassign(f)
