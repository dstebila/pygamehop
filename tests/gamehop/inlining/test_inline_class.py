import ast
import inspect
import unittest

import gamehop.inlining
import gamehop.verification.canonicalization

class class_with_no_methods(object):
    def __init__(self):
        self.myarg = 0
def f_class_with_no_methods(x: class_with_no_methods) -> int:
    return x.myarg
def f_class_with_no_methods_expected_result() -> int:
    xⴰmyarg = 0
    return xⴰmyarg

class class_init_has_args(object):
    def __init__(self, a: int, b: int):
        self.myarg = a + b
def f_class_init_has_args(x: class_with_no_methods) -> int:
    return x.myarg
def f_class_init_has_args_expected_result(xⴰinitⴰa: int, xⴰinitⴰb: int) -> int:
    xⴰmyarg = xⴰinitⴰa + xⴰinitⴰb
    return xⴰmyarg

class class_with_a_method(object):
    def __init__(self):
        self.myarg = 0
    def m(self, y: int):
        self.myarg = y
        a = 2
def f_class_with_a_method(x: class_with_a_method, y: int) -> int:
    x.m(y)
    return x.myarg
def f_class_with_a_method_expected_result(y: int) -> int:
    xⴰmyarg = 0
    xⴰmyarg = y
    xⴰmᴠ1ⴰa = 2
    return xⴰmyarg

class class_with_no_init(object):
    def m(self, y: int):
        self.myarg = y
        return self.myarg
def f_class_with_no_init(x: class_with_no_init, y: int) -> int:
    z = x.m(y)
    return x.myarg
def f_class_with_no_init_expected_result(y: int) -> int:
    xⴰmyarg = y
    z = xⴰmyarg
    return xⴰmyarg

class class_method_with_no_argument():
    def m(self):
        return 1 + 0
def f_class_method_with_no_argument(x: class_method_with_no_argument) -> int:
    z = x.m()
    return z
def f_class_method_with_no_argument_expected_result() -> int:
    z = 1 + 0
    return z

def f_inlines_same_class_twice(x: class_with_a_method, y: int, z: class_with_a_method) -> int:
    x.m(y)
    z.m(y)
    return x.myarg
def f_inlines_same_class_twice_expected_result(y: int) -> int:
    zⴰmyarg = 0
    xⴰmyarg = 0
    xⴰmyarg = y
    xⴰmᴠ1ⴰa = 2
    zⴰmyarg = y
    zⴰmᴠ1ⴰa = 2
    return xⴰmyarg

def f_calls_method_twice(x: class_with_a_method, y: int) -> int:
    x.m(y)
    x.m(7)
    return x.myarg
def f_calls_method_twice_expected_result(y: int) -> int:
    xⴰmyarg = 0
    xⴰmyarg = y
    xⴰmᴠ1ⴰa = 2
    xⴰmyarg = 7
    xⴰmᴠ2ⴰa = 2
    return xⴰmyarg

class class_with_double_attributing(object):
    def m(self, x):
        y = self.a.b(3)
        return y
def f_double_attributing(x: class_with_double_attributing):
    z = x.m(7)
def f_double_attributing_expected_result():
    xⴰmᴠ1ⴰy = xⴰa.b(3)
    z = xⴰmᴠ1ⴰy

def f_intermediate_value_helper(x):
    return x + 1
class class_intermediate_value():
    def __init__(self):
        self.x = 1
def f_intermediate_value(v: class_intermediate_value):
    y = f_intermediate_value_helper(v.x)
    return y
def f_intermediate_value_expected_result():
    y = f_intermediate_value_helper(1)
    return y


def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestInlineClass(unittest.TestCase):
    def test_class_with_no_methods(self):
        self.assertEqual(
            gamehop.inlining.inline_class(f_class_with_no_methods, 'x', class_with_no_methods),
            expected_result(f_class_with_no_methods_expected_result))
    def test_class_init_has_args(self):
        self.assertEqual(
            gamehop.inlining.inline_class(f_class_init_has_args, 'x', class_init_has_args),
            expected_result(f_class_init_has_args_expected_result))
    def test_class_with_a_method(self):
        self.assertEqual(
            gamehop.inlining.inline_class(f_class_with_a_method, 'x', class_with_a_method),
            expected_result(f_class_with_a_method_expected_result))
    def test_class_with_no_init(self):
        self.assertEqual(
            gamehop.inlining.inline_class(f_class_with_no_init, 'x', class_with_no_init),
            expected_result(f_class_with_no_init_expected_result))
    def test_class_method_with_no_argument(self):
        self.assertEqual(
            gamehop.inlining.inline_class(f_class_method_with_no_argument, 'x', class_method_with_no_argument),
            expected_result(f_class_method_with_no_argument_expected_result))
    def test_inlines_same_class_twice(self):
        f = f_inlines_same_class_twice
        f = gamehop.inlining.inline_class(f, 'x', class_with_a_method)
        f = gamehop.inlining.inline_class(f, 'z', class_with_a_method)
        self.assertEqual(
            f,
            expected_result(f_inlines_same_class_twice_expected_result))
    def test_calls_method_twice(self):
        self.assertEqual(
            gamehop.inlining.inline_class(f_calls_method_twice, 'x', class_with_a_method),
            expected_result(f_calls_method_twice_expected_result))
    def test_double_attributing(self):
        self.assertEqual(
            gamehop.inlining.inline_class(f_double_attributing, 'x', class_with_double_attributing),
            expected_result(f_double_attributing_expected_result))
    def test_intermediate_value(self):
        step1 = gamehop.inlining.inline_class(f_intermediate_value, 'v', class_intermediate_value)
        step2 = gamehop.inlining.internal.get_function_def(step1)
        gamehop.verification.canonicalization.collapse_useless_assigns(step2)
        self.assertEqual(
            ast.unparse(step2),
            expected_result(f_intermediate_value_expected_result))
