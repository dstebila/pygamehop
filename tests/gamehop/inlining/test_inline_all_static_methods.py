import ast
import inspect
import unittest

import gamehop.inlining

def expected_result(f):
    fdef = gamehop.utils.get_function_def(f)
    fdef.name = fdef.name.replace('_expected_result', '')
    return ast.unparse(fdef)

class TestInlineAllMethodsIntoFunction(unittest.TestCase):

    def test_basic(self):
        class C():
            @staticmethod
            def A(x, y): 
                w = x + y
                return w
            @staticmethod
            def B(x, y, z): return x * y * z
        def f(x):
            y = C.A(x, x)
            z = C.B(1, 2, x)
            r = 2
        def f_expected_result(x):
            C_Aᴠ1ⴰw = x + x
            y = C_Aᴠ1ⴰw
            z = 1 * 2 * x
            r = 2
        self.assertEqual(
            gamehop.inlining.inline_all_static_method_calls(C, f),
            expected_result(f_expected_result))
