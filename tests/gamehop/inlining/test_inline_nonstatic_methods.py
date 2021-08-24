import ast
import inspect
import unittest

import gamehop.inlining

def expected_result(f):
    fdef = gamehop.utils.get_function_def(f)
    fdef.name = fdef.name.replace('_expected_result', '')
    return ast.unparse(fdef)

class TestInlineNonStaticMethods(unittest.TestCase):

    def test_nonstatic_method(self):
        class Foo():
            def F(self, a, b):
                d = a + b + self.c
                return d
        def f(x):
            y = 1
            r = x.F(y, 3)
            return r
        def f_expected_result(x):
            y = 1
            x_Fᴠ1ⴰd = y + 3 + x.c
            r = x_Fᴠ1ⴰd
            return r
        self.assertEqual(
            gamehop.inlining.inline_all_nonstatic_method_calls('x', Foo, f),
            expected_result(f_expected_result))
