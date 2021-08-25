import ast
import inspect
import unittest

import gamehop.inlining

def expected_result(f):
    fdef = gamehop.utils.get_function_def(f)
    fdef.name = fdef.name.replace('_expected_result', '')
    return ast.unparse(fdef)

class TestInlineAllInnerClassInitCallsIntoFunction(unittest.TestCase):

    def test_basic(self):
        self.maxDiff = None
        class C():
            class D():
                def __init__(self, a, b):
                    self.x = a
                    self.y = b
        def f(x):
            z = C.D(3, int(4))
            return z
        def f_expected_result(x):
            z = C.D.__new__(C.D)
            z.x = 3
            z.y = int(4)
            return z
        print(gamehop.inlining.inline_all_inner_class_init_calls(C, f))
        self.assertEqual(
            gamehop.inlining.inline_all_inner_class_init_calls(C, f),
            expected_result(f_expected_result))

    def test_extra(self):
        self.maxDiff = None
        class C():
            class D():
                def __init__(self, a, b):
                    self.x = a
                    w = a + b
                    self.y = w
        def f(x):
            z = C.D(3, 2)
            return z
        def f_expected_result(x):
            z = C.D.__new__(C.D)
            z.x = 3
            C_D___new__v1_w = 3 + 2
            z.y = C_D___new__v1_w
            return z
        print(gamehop.inlining.inline_all_inner_class_init_calls(C, f))
        self.assertEqual(
            gamehop.inlining.inline_all_inner_class_init_calls(C, f),
            expected_result(f_expected_result))

TestInlineAllInnerClassInitCallsIntoFunction().test_basic()
