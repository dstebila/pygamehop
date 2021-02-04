import ast
import inspect
import unittest

import gamehop.inlining

class class_with_no_methods(object):
    def __init__(self):
        self.myarg = 0
def f_class_with_no_methods(x: class_with_no_methods) -> int:
    return x.myarg
def f_class_with_no_methods_expected_result() -> int:
    v_x_myarg = 0
    return v_x_myarg

class class_init_has_args(object):
    def __init__(self, a: int, b: int):
        self.myarg = a + b
def f_class_init_has_args(x: class_with_no_methods) -> int:
    return x.myarg
def f_class_init_has_args_expected_result(v_x_init_a: int, v_x_init_b: int) -> int:
    v_x_myarg = v_x_init_a + v_x_init_b
    return v_x_myarg

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
    v_x_myarg = 0
    v_x_myarg = y
    v_x_m_1_a = 2
    return v_x_myarg

class class_with_no_init(object):
    def m(self, y: int):
        self.myarg = y
        return self.myarg
def f_class_with_no_init(x: class_with_no_init, y: int) -> int:
    z = x.m(y)
    return x.myarg
def f_class_with_no_init_expected_result(y: int) -> int:
    v_x_myarg = y
    v_x_m_1_v_retval = v_x_myarg
    z = v_x_m_1_v_retval
    return v_x_myarg

class class_method_with_no_argument():
    def m(self):
        return 1 + 0
def f_class_method_with_no_argument(x: class_method_with_no_argument) -> int:
    z = x.m()
    return z
def f_class_method_with_no_argument_expected_result() -> int:
    v_x_m_1_v_retval = 1 + 0
    z = v_x_m_1_v_retval
    return z

def f_inlines_same_class_twice(x: class_with_a_method, y: int, z: class_with_a_method) -> int:
    x.m(y)
    z.m(y)
    return x.myarg
def f_inlines_same_class_twice_expected_result(y: int) -> int:
    v_z_myarg = 0
    v_x_myarg = 0
    v_x_myarg = y
    v_x_m_1_a = 2
    v_z_myarg = y
    v_z_m_1_a = 2
    return v_x_myarg


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
