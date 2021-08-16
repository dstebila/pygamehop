import ast
import inspect
import unittest

import gamehop.inlining

def expected_result(f):
    fdef = gamehop.utils.get_function_def(f)
    fdef.name = fdef.name.replace('_expected_result', '')
    return ast.unparse(fdef)

class TestInlineArgumentIntoFunction(unittest.TestCase):

    def test_arg_not_found(self):
        def f(x): print(x)
        with self.assertRaisesRegex(KeyError, "Argument y not found in list of arguments to function f"):
            gamehop.inlining.inline_argument_into_function('y', True, f)

    def test_bool(self):
        def f(x, y): print(x)
        def f_expected_result(y): print(True)
        self.assertEqual(
            gamehop.inlining.inline_argument_into_function('x', True, f),
            expected_result(f_expected_result))

    def test_float(self):
        def f(x): print(x)
        def f_expected_result(): print(3.14152)
        self.assertEqual(
            gamehop.inlining.inline_argument_into_function('x', 3.14152, f),
            expected_result(f_expected_result))
    
    def test_int(self):
        def f(x): print(x)
        def f_expected_result(): print(42)
        self.assertEqual(
            gamehop.inlining.inline_argument_into_function('x', 42, f),
            expected_result(f_expected_result))
    
    def test_str(self):
        def f(x): print(x)
        def f_expected_result(): print("potato")
        self.assertEqual(
            gamehop.inlining.inline_argument_into_function('x', 'potato', f),
            expected_result(f_expected_result))
    
    def test_tuple(self):
        def f(x, y): print(x)
        def f_expected_result(y): print((1, 2, 3))
        self.assertEqual(
            gamehop.inlining.inline_argument_into_function('x', (1, 2, 3), f),
            expected_result(f_expected_result))

    def test_tuple_ast(self):
        def f(x, y): print(x)
        def f_expected_result(y): print((1, 2, 3))
        tupleast = ast.Tuple([ast.Constant(1), ast.Constant(2), ast.Constant(3)], ctx=ast.Load())
        self.assertEqual(
            gamehop.inlining.inline_argument_into_function('x', tupleast, f),
            expected_result(f_expected_result))

    def test_f_as_string(self):
        str_bool_f = "def f(x, y): print(x)"
        def f_expected_result(y): print(True)
        self.assertEqual(
            gamehop.inlining.inline_argument_into_function('x', True, str_bool_f),
            expected_result(f_expected_result))

    def test_assigned(self):
        def f(x):
            print(x)
            x = 123
        with self.assertRaisesRegex(ValueError, "Error inlining argument x into function f: x is assigned to in the body of f"):
            gamehop.inlining.inline_argument_into_function('x', True, f)
