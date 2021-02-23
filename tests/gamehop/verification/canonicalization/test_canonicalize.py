import ast
import inspect
import unittest

import gamehop
import gamehop.verification

def f_inline_function_order_helper(x):
    return x + 1
class class_inline_function_order():
    def f(self):
        return f_inline_function_order_helper(1)        
def f_inline_function_order(v: class_inline_function_order):
    x = v.f()
    y = v.f()
    return y + 2 * x
def f_inline_function_order_expected_result():
    y = f_inline_function_order_helper(1)
    x = f_inline_function_order_helper(1)
    return y + 2 * x

def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestCanonicalize(unittest.TestCase):
    def test_inline_function_order(self):
        f = gamehop.inline(f_inline_function_order, class_inline_function_order, 'v')
        f = gamehop.verification.canonicalize_function(f)
        g = gamehop.verification.canonicalize_function(expected_result(f_inline_function_order_expected_result))
        self.assertEqual(
            f,
            g
        )

g = gamehop.verification.canonicalize_function(expected_result(f_inline_function_order_expected_result))
print(g)