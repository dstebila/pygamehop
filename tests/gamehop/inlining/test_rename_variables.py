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

def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestRenameVariables(unittest.TestCase):
    def test_basic(self):
        fdef = gamehop.inlining.internal.get_function_def(f_basic)
        mappings = {'x': 'v_1', 'y': 'v_2', 'a': 'v_3'}
        result = gamehop.inlining.internal.rename_variables(fdef, mappings)
        self.assertEqual(
            ast.unparse(result),
            expected_result(f_basic_expected_result))
    def test_name_collision_in_body(self):
        fdef = gamehop.inlining.internal.get_function_def(f_basic)
        mappings = {'x': 'a'}
        with self.assertRaises(ValueError):
            gamehop.inlining.internal.rename_variables(fdef, mappings)
    def test_name_collision_in_args(self):
        fdef = gamehop.inlining.internal.get_function_def(f_basic)
        mappings = {'x': 'y'}
        with self.assertRaises(ValueError):
            gamehop.inlining.internal.rename_variables(fdef, mappings)
