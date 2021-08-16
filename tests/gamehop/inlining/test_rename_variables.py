import ast
import inspect
import unittest

import gamehop.inlining.internal

def f_basic(x, y):
    a = 7
    b = len(x)
    c = b + y
    y = 4 + a
    return y + b
def f_basic_expected_result(v_1, v_2):
    v_3 = 7
    b = len(v_1)
    c = b + v_2
    v_2 = 4 + v_3
    return v_2 + b
def f_attribute(a):
    a.b = 7
def f_attribute_expected_result(z):
    z.b = 7

def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestRenameVariables(unittest.TestCase):
    def test_basic(self):
        mappings = {'x': 'v_1', 'y': 'v_2', 'a': 'v_3'}
        self.assertEqual(
            ast.unparse(gamehop.utils.rename_variables(f_basic, mappings)),
            expected_result(f_basic_expected_result))
    def test_name_collision_in_body(self):
        mappings = {'x': 'a'}
        with self.assertRaises(ValueError):
            gamehop.utils.rename_variables(f_basic, mappings)
    def test_name_collision_in_args(self):
        mappings = {'x': 'y'}
        with self.assertRaises(ValueError):
            gamehop.utils.rename_variables(f_basic, mappings)
    def test_attribute(self):
        mappings = {'a': 'z'}
        self.assertEqual(
            ast.unparse(gamehop.utils.rename_variables(f_attribute, mappings)),
            expected_result(f_attribute_expected_result))
