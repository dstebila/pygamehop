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
    v_x_self_myarg = 0
    return v_x_self_myarg

class class_init_has_args(object):
    def __init__(self, a: int, b: int):
        self.myarg = a + b
def f_class_init_has_args(x: class_with_no_methods) -> int:
    return x.myarg
def f_class_init_has_args_expected_result(v_x_init_a: int, v_x_init_b: int) -> int:
    v_x_self_myarg = v_x_init_a + v_x_init_b
    return v_x_self_myarg

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
